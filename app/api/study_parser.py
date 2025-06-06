#! /usr/bin/env python

'''
Adapted from https://github.com/IDR/idr-utils/blob/1ba5e3810751b6df04ae0d0472a7a09c852d7e7a/pyidr/study_parser.py
'''

from builtins import str
from builtins import zip
from builtins import range
from builtins import object
from argparse import ArgumentParser
import glob
import json
import logging
import os
import re
import sys

from getpass import getpass

TYPES = ["Experiment", "Screen"]


class Key(object):

    def __init__(self, pattern, scope, optional=False):
        self.pattern = pattern
        self.scope = scope
        self.optional = optional


KEYS = (
    # OPTIONAL_KEYS["Study"]
    Key(r'Comment\[IDR Study Accession\]', 'Study'),
    Key('Study Title', 'Study'),
    Key('Study Description', 'Study'),
    Key('Study Type', 'Study'),
    Key('Study Type Term Source REF', 'Study', optional=True),
    Key('Study Type Term Accession', 'Study', optional=True),
    Key('Study Publication Title', 'Study'),
    Key('Study Author List', 'Study'),
    Key('Study Organism', 'Study', optional=True),
    Key('Study Organism Term Source REF', 'Study', optional=True),
    Key('Study Organism Term Accession', 'Study', optional=True),
    # OPTIONAL_KEYS["Study"]
    Key('Study Version History', 'Study', optional=True),
    Key('Study BioStudies Accession', 'Study', optional=True),
    Key('Study BioImage Archive Accession', 'Study', optional=True),
    Key('Study EMPIAR Accession', 'Study', optional=True),
    Key('Study Publication Preprint', 'Study', optional=True),
    Key('Study PubMed ID', 'Study', optional=True),
    Key('Study PMC ID', 'Study', optional=True),
    Key('Study DOI', 'Study', optional=True),
    Key('Study Copyright', 'Study', optional=True),
    Key('Study License', 'Study', optional=True),
    Key('Study License URL', 'Study', optional=True),
    Key('Study Data Publisher', 'Study', optional=True),
    Key('Study Data DOI', 'Study', optional=True),
    Key('Study Experiments Number', 'Study', optional=True),
    Key('Study Screens Number', 'Study', optional=True),
    Key('Study External URL', 'Study', optional=True),
    Key('Study Public Release Date', 'Study'),
    Key('Study Person Last Name', 'Study', optional=True),
    Key('Study Person First Name', 'Study', optional=True),
    Key('Study Person Email', 'Study', optional=True),
    Key('Study Person Address', 'Study', optional=True),
    Key('Study Person Roles', 'Study', optional=True),
    Key('Study Person ORCID', 'Study', optional=True),
    Key('Study Key Words', 'Study', optional=True),
    Key('Term Source Name', 'Study', optional=True),
    Key('Term Source URI', 'Study', optional=True),
    # MANDATORY_KEYS["Experiment"]
    Key(r'Comment\[IDR Experiment Name\]', 'Experiment'),
    Key('Experiment Description', 'Experiment'),
    Key('Experiment Sample Type', 'Experiment'),
    Key('Experiment Imaging Method', 'Experiment'),
    Key('Experiment Number', 'Experiment'),
    # OPTIONAL_KEYS["Experiment"]
    Key('Experiment Data DOI', 'Experiment', optional=True),
    Key("Experiment Data Publisher", 'Experiment', optional=True),
    Key('Experiment Organism', 'Experiment', optional=True),
    Key('Experiment Organism Term Source REF', 'Experiment', optional=True),
    Key('Experiment Organism Term Accession', 'Experiment', optional=True),
    # MANDATORY_KEYS["Screen"]
    Key(r'Comment\[IDR Screen Name\]', 'Screen'),
    Key('Screen Description', 'Screen'),
    Key('Screen Sample Type', 'Screen'),
    Key('Screen Imaging Method', 'Screen'),
    Key('Screen Number', 'Screen'),
    Key('Screen Type', 'Screen'),
    # OPTIONAL_KEYS["Screen"]
    Key('Screen Data DOI', 'Screen', optional=True),
    Key('Screen Data Publisher', 'Screen', optional=True),
    Key('Screen Technology Type', 'Screen', optional=True),
    Key('Screen Organism', 'Screen', optional=True),
    Key('Screen Organism Term Source REF', 'Screen', optional=True),
    Key('Screen Organism Term Accession', 'Screen', optional=True),
    Key('Screen Sample Type', 'Screen', optional=True),
    Key('Screen Size', 'Screen', optional=True),
    Key('Screen Imaging Method Term Source REF', 'Screen', optional=True),
    Key('Screen Imaging Method Term Accession', 'Screen', optional=True),
    Key('Screen Technology Type Term Source REF', 'Screen', optional=True),
    Key('Screen Technology Type Term Accession', 'Screen', optional=True),
    Key('Screen Type Term Source REF', 'Screen', optional=True),
    Key('Screen Type Term Accession', 'Screen', optional=True),
)

DOI_PATTERN = re.compile(
    r"(?P<url>https?://(dx.)?doi.org/)?(?P<id>\b10\.\d+/\S+\b)")
STUDY_NS = "idr.openmicroscopy.org/study/info"
COMPONENTS_NS = "idr.openmicroscopy.org/study/components"


def connect(hostname, username, password):
    """
    Connect to an OMERO server
    :param hostname: Host name
    :param username: User
    :param password: Password
    :return: Connected BlitzGateway
    """
    conn = BlitzGateway(username, password,
                        host=hostname, secure=True)
    conn.connect()
    conn.c.enableKeepAlive(60)
    return conn


class StudyError(Exception):
    pass


class StudyParser(object):

    def __init__(self, study_file):
        self._study_file = study_file
        self._dir = os.path.dirname(self._study_file)
        self.log = logging.getLogger("pyidr.study_parser.StudyParser")
        # Snyk: Unsanitized input from a command line argument flows into open,
        # where it is used as a path. This may result in a Path Traversal vulnerability
        # and allow an attacker to read arbitrary files.
        # ** But this is a local script and the study file to analyze will be on ./data,
        # which is on the root /data on the docker
        with open(self._study_file, 'r', encoding='utf-8',
                  errors='ignore') as f:
            self.log.info("Parsing %s" % self._study_file)
            self._study_lines = f.readlines()
            self._study_lines_used = [
                [] for x in range(len(self._study_lines))]

        self.study = self.parse("Study")

        self.parse_publications()
        self.study.update(self.parse_data_doi(self.study, "Study Data DOI"))

        self.components = []

        # Find number of screens and experiments
        n_screens = int(self.study.get('Study Screens Number', 0))
        n_experiments = int(self.study.get('Study Experiments Number', 0))
        self.log.debug("Expecting %s screen(s) and %s experiment(s)" %
                       (n_screens, n_experiments))
        if n_screens > 0 and n_experiments > 0:
            component_regexp = '(Screen|Experiment)'
        elif n_screens > 0:
            component_regexp = '(Screen)'
        elif n_experiments > 0:
            component_regexp = '(Experiment)'
        else:
            raise Exception("Not enough screens and/or experiments")

        # Find all study components in order
        for i in range(n_screens + n_experiments):
            lines, component_type = self.get_lines(i + 1, component_regexp)
            d = self.parse(component_type, lines=lines)
            d.update({'Type': component_type})
            d.update(self.study)
            doi = self.parse_data_doi(d, "%s Data DOI" % component_type)
            if doi:
                d.update(doi)
            self.parse_annotation_file(d)
            self.parse_organism(d)
            self.components.append(d)

        if not self.components:
            raise Exception("Need to define at least one screen or experiment")

    def get_value(self, key, expr=".*", fail_on_missing=True, lines=None):
        pattern = re.compile("^%s\t(%s)" % (key, expr))
        if lines:
            # Fake space since we don't know what the caller is passing
            used = [[] for x in range(len(lines))]
        else:
            lines = self._study_lines
            used = self._study_lines_used
        for idx, line in enumerate(lines):
            m = pattern.match(line)
            if m:
                used[idx].append(("get_value", key, expr))
                return m.group(1).rstrip()
        if fail_on_missing:
            raise Exception("Could not find value for key %s " % key)

    def parse(self, scope, lines=None):
        d = {}
        mandatory_keys = [x.pattern for x in KEYS
                          if x.scope == scope and not x.optional]
        optional_keys = [x.pattern for x in KEYS
                         if x.scope == scope and x.optional]
        for key in mandatory_keys:
            d[key] = self.get_value(key, lines=lines)
        for key in optional_keys:
            value = self.get_value(key, fail_on_missing=False, lines=lines)
            if value:
                d[key] = value
        return d

    def get_lines(self, index, component_regexp):
        self.log.debug("Parsing %s %g" % (component_regexp, index))
        PATTERN = re.compile(r"^%s Number\t(\d+)" % component_regexp)
        found = False
        lines = []
        component_type = None
        for idx, line in enumerate(self._study_lines):
            m = PATTERN.match(line)
            if m:
                if int(m.group(2)) == index and found:
                    raise Exception("Duplicate component %g" % index)
                elif int(m.group(2)) == index and not found:
                    found = True
                    component_type = m.group(1)
                elif int(m.group(2)) != index and found:
                    return lines, component_type
            if found:
                self._study_lines_used[idx].append(("get_lines", index))
                lines.append(line)
        if not lines:
            raise Exception("Could not find %s %g" % (component_regexp, index))
        return lines, component_type

    def parse_annotation_file(self, component):
        import glob

        accession_number = self.get_study_accession()
        pattern = re.compile(r"(%s-\w+(-\w+)?)/(\w+)$" % accession_number)
        name = component[r"Comment\[IDR %s Name\]" % component["Type"]]
        m = pattern.match(name)
        if not m:
            raise Exception("Unmatched name %s" % name)

        # Check for annotation.csv file
        component_path = os.path.join(self._dir, m.group(3))
        basename = "%s-%s-annotation" % (accession_number, m.group(3))

        # Generate GitHub annotation URL
        if os.path.exists(os.path.join(self._dir, ".git")):
            base_gh_url = "https://github.com/IDR/%s/blob/HEAD/%s" % (
                m.group(1), m.group(3))
        else:
            base_gh_url = (
                "https://github.com/IDR/idr-metadata/blob/HEAD/%s" % name)

        # Try to find single annotation file in root directory
        for extension in ['.csv', '.csv.gz']:
            annotation_filename = "%s%s" % (basename, extension)
            annotation_path = os.path.join(component_path, annotation_filename)
            if os.path.exists(annotation_path):
                component["Annotations"] = [{
                    "Annotation File": "%s %s" % (
                        annotation_filename, base_gh_url + "/%s" %
                        annotation_filename)}]
                return

        component["Annotations"] = []
        annotation_filenames = sorted(glob.glob(os.path.join(
            component_path, "**", "%s.csv.gz" % basename)))
        for annotation_filename in annotation_filenames:
            component["Annotations"].append({
                "Annotation File": "%s %s" % (
                    os.path.basename(annotation_filename),
                    base_gh_url + "%s" %
                    annotation_filename[len(component_path):])
            })
        return

    def parse_publications(self):

        titles = self.study['Study Publication Title'].split('\t')
        authors = self.study['Study Author List'].split('\t')
        assert len(titles) == len(authors), (
            "Mismatching publication titles and authors")
        if titles == [''] and authors == ['']:
            return

        publications = [{"Title": title, "Author List": author}
                        for title, author in zip(titles, authors)]

        def parse_ids(key, pattern):
            if key not in self.study:
                return
            split_ids = self.study[key].split('\t')
            key2 = key.strip("Study ")
            for i in range(len(split_ids)):
                if not split_ids[i]:
                    continue
                m = pattern.match(split_ids[i])
                if not m:
                    raise Exception("Invalid %s: %s" % (key2, split_ids[i]))
                publications[i][key2] = m.group("id")

        parse_ids("Study PubMed ID", re.compile(r"(?P<id>\d+)"))
        parse_ids("Study PMC ID", re.compile(r"(?P<id>PMC\d+)"))
        parse_ids("Study DOI", DOI_PATTERN)

        self.study["Publications"] = publications

    @staticmethod
    def parse_data_doi(d, key):
        if key not in d:
            return {}
        m = DOI_PATTERN.match(d[key])
        if not m:
            raise Exception(
                "Invalid Data DOI: %s" % d[key])
        return {"Data DOI": #m.group("id")
                            d[key]}

    @staticmethod
    def parse_organism(component):
        key = '%s Organism' % component['Type']
        if 'Study Organism' in component and key in component:
            raise Exception("Organism defined both at the study and %s level"
                            % component['Type']) #TODO: Change this to save organism at study level and organism at screen/experiment level instead of raising an exception 
        elif 'Study Organism' not in component and key not in component:
            raise Exception("Missing organism field")
        elif 'Study Organism' in component:
            component[key] = component['Study Organism']
        return

    def get_study_accession(self):
        return self.study[r"Comment\[IDR Study Accession\]"]

    def get_study_name(self):
        study_name = None
        for component in self.components:
            name = component[r"Comment\[IDR %s Name\]" % component["Type"]]
            if study_name is None:
                study_name = name.split("/")[0]
            else:
                assert study_name == name.split("/")[0], (
                    "%s != %s" % (study_name, name.split("/")[0]))
        return study_name


class Formatter(object):

    EXPERIMENT_SAMPLE_PAIRS = [
        ('Sample Type', "%(Experiment Sample Type)s"),
        ('Organism', "%(Experiment Organism)s"),
    ]
    SCREEN_SAMPLE_PAIRS = [
        ('Sample Type', "%(Screen Sample Type)s"),
        ('Organism', "%(Screen Organism)s"),
    ]
    EXPERIMENT_TECHNOLOGY_PAIRS = [
        ('Study Type', "%(Study Type)s"),
        ('Imaging Method', "%(Experiment Imaging Method)s"),
    ]
    SCREEN_TECHNOLOGY_PAIRS = [
        ('Study Type', "%(Study Type)s"),
        ('Screen Type', "%(Screen Type)s"),
        ('Screen Technology Type', "%(Screen Technology Type)s"),
        ('Imaging Method', "%(Screen Imaging Method)s"),
    ]
    PUBLICATION_PAIRS = [
        ('Publication Title', "%(Title)s"),
        ('Publication Authors', "%(Author List)s"),
        ('PubMed ID', "%(PubMed ID)s "
         "https://www.ncbi.nlm.nih.gov/pubmed/%(PubMed ID)s"),
        ('PMC ID',
         "%(PMC ID)s https://www.ncbi.nlm.nih.gov/pmc/articles/%(PMC ID)s"),
        ('Publication DOI', "%(DOI)s https://doi.org/%(DOI)s"),
    ]
    BOTTOM_PAIRS = [
        ('Release Date', '%(Study Public Release Date)s'),
        ('License', "%(Study License)s %(Study License URL)s"),
        ('Copyright', "%(Study Copyright)s"),
        ('Data Publisher', "%(Study Data Publisher)s"),
        ('Data DOI', "%(Data DOI)s "
         "https://doi.org/%(Data DOI)s"),
        ('External URL', "%(Study External URL)s"),
        ('BioStudies Accession', "%(Study BioImage Archive Accession)s"
         " https://www.ebi.ac.uk/biostudies/studies/"
         "%(Study BioImage Archive Accession)s"),
        ('BioStudies Accession', "%(Study BioStudies Accession)s"
         " https://www.ebi.ac.uk/biostudies/studies/"
         "%(Study BioStudies Accession)s"),
        ('EMPIAR Accession', "%(Study EMPIAR Accession)s"
         " https://dx.doi.org/10.6019/%(Study EMPIAR Accession)s"),
    ]
    ANNOTATION_PAIRS = [('Annotation File', "%(Annotation File)s")]

    def __init__(self, parser, inspect=False):
        self.log = logging.getLogger("pyidr.study_parser.Formatter")
        self.parser = parser
        self.basedir = os.path.dirname(parser._study_file)
        self.inspect = inspect
        self.m = {
          "name": self.parser.get_study_name(),
          "accession": self.parser.get_study_accession(),
          "source": self.parser._study_file,
          "experiments": [],
          "screens": [],
        }

        # Serialize experiments/screens
        for component in self.parser.components:
            name = component[r"Comment\[IDR %s Name\]" % component["Type"]]
            d = {
              "name": name,
              "description": self.generate_description(component),
              "map": self.generate_annotation(component),
            }
            if self.inspect:
                self.log.info("Inspect the internals of %s" % self.basedir)
                path = "%s/%s/*" % (self.basedir, name.split("/")[-1])
                d["files"] = glob.glob(path)
            self.m["%ss" % component['Type'].lower()].append(d)

        # Add top-level study
        d = {
            "description": self.generate_description(self.parser.study),
            "map": self.generate_annotation(self.parser.study),
        }
        self.m.update(d)

    def __str__(self):
        return json.dumps(self.m, indent=4, sort_keys=True)

    def generate_description(self, component):
        """Generate the description of the study/experiment/screen"""
        publication_title = ""
        if component["Study Publication Title"]:
            # Only display the first publication
            publication_title = (
                "Publication Title\n%(Study Publication Title)s" %
                component).split('\t')[0] + "\n\n"
        if "Type" in component:
            key = "%s Description" % component["Type"]
        else:
            key = "Study Description"
        component_title = (
            "%s\n%s" % (key, component[key]))
        if "Study Version History" in component:
            history = ("\n\nVersion History\n%s" %
                       component["Study Version History"])
        else:
            history = ""

        return publication_title + component_title + history

    def generate_annotation(self, component):
        """Generate the map annotation of the study/experiment/screen"""

        def add_key_values(d, pairs):
            for key, formatter in pairs:
                try:
                    value = formatter % d
                    for v in value.split('\t'):
                        s.append({'%s' % key: v})
                except KeyError as e:
                    self.log.debug("Missing %s" % str(e))

        s = []
        if component.get("Type", None) == "Experiment":
            add_key_values(component, self.EXPERIMENT_SAMPLE_PAIRS)
        elif component.get("Type", None) == "Screen":
            add_key_values(component, self.SCREEN_SAMPLE_PAIRS)

        # Only add Study title if not redundant with Publication Title
        publication_titles = [
            x['Title'] for x in component.get("Publications", [])]
        study_title = component.get("Study Title", None)
        if study_title is not None and study_title not in publication_titles:
            add_key_values(component, [('Study Title', "%(Study Title)s")])

        if component.get("Type", None) == "Experiment":
            add_key_values(component, self.EXPERIMENT_TECHNOLOGY_PAIRS)
        elif component.get("Type", None) == "Screen":
            add_key_values(component, self.SCREEN_TECHNOLOGY_PAIRS)

        for publication in component.get("Publications", []):
            add_key_values(publication, self.PUBLICATION_PAIRS)
        add_key_values(component, self.BOTTOM_PAIRS)
        for annotation in component.get("Annotations", []):
            add_key_values(annotation, self.ANNOTATION_PAIRS)
        return s

    def check_object(self, obj, d, update=False):
        """Check description and map of individual object on OMERO server"""
        

        status = True
        self.log.info("Checking %s %s" % (obj.OMERO_CLASS, obj.name))

        if obj.description != d["description"]:
            status = False
            if update:
                self.log.info("Updating description")
                self.log.debug("previous:%s" % obj.description,)
                self.log.debug("new:%s" % d["description"])
                obj.setDescription(d["description"])
                obj.save()
            else:
                self.log.error("Mismatching description")
                self.log.debug("current:%s" % obj.description,)
                self.log.debug("expected:%s" % d["description"])

        for ann in obj.listAnnotations(
                ns=omero.constants.metadata.NSCLIENTMAPANNOTATION):
            self.log.error("Found client map annotation")
            status = False
            if update:
                self.log.info("Deleting client map annotation")
                ann._conn.deleteObjects('Annotation', [ann.id])

        expected_pairs = [(k, v) for i in d["map"] for k, v in i.items()]
        status = self.check_annotation(
            obj, expected_pairs, STUDY_NS, update=update)
        return status

    def check_annotation(self, obj, value, namespace, update=False):


        status = True
        anns = list(obj.listAnnotations(ns=namespace))
        if len(anns) > 1:
            self.log.error(
                "Found multiple annotations with the %s namespace" % STUDY_NS)
            status = False
        elif len(anns) == 0:
            if update:
                self.log.info("Creating map annotation")
                m = MapAnnotationWrapper(conn=obj._conn)
                m.setNs(rstring(namespace))
                m.setValue(value)
                m.save()
                obj.linkAnnotation(m)
            else:
                self.log.error("No map annotation found")
        elif anns[0].getValue() != value:
            status = False
            if update:
                self.log.info("Updating map annotation")
                self.log.debug("previous:%s" % anns[0].getValue())
                self.log.debug("new:%s" % value)
                anns[0].setValue(value)
                anns[0].save()
            else:
                self.log.error("Mismatching annotation")
                self.log.debug("current:%s" % anns[0].getValue())
                self.log.debug("expected:%s" % value)
        return status

    def check_study(self, gateway, update=False):
        """Check all components of the study"""

        WEBCLIENT_URL = "https://idr.openmicroscopy.org/webclient/"
        objects = []
        components_map = []
        for experiment in self.m["experiments"]:
            project = gateway.getObject(
                "Project", attributes={"name": experiment["name"]})
            self.check_object(project, experiment, update=update)
            objects.append(project)
            name = "Experiment " + experiment["name"][-1]
            components_map.append(
                (name, "%s?show=project-%s" % (WEBCLIENT_URL, project.id)))

        for s in self.m["screens"]:
            screen = gateway.getObject(
                "Screen", attributes={"name": s["name"]})
            self.check_object(screen, s, update=update)
            objects.append(screen)
            name = "Screen " + s["name"][-1]
            components_map.append(
                (name, "%s?show=screen-%s" % (WEBCLIENT_URL, screen.id)))

        if len(objects) == 1:
            return

        found_toplevel = False
        project = gateway.getObject(
            "Project", attributes={"name": self.m["name"]})
        if project is not None:
            found_toplevel = True
            self.check_object(project, self.m, update=update)
            objects.append(project)
            components_map.append(
                ("Overview",
                 "%s?show=project-%s" % (WEBCLIENT_URL, project.id)))
        else:
            screen = gateway.getObject(
                "Screen", attributes={"name": self.m["name"]})
            if screen is not None:
                found_toplevel = True
                self.check_object(screen, self.m, update=update)
                objects.append(screen)
                components_map.append(
                    ("Overview",
                     "%s?show=screen-%s" % (WEBCLIENT_URL, screen.id)))

        if not found_toplevel:
            self.log.error(f'Top level container {self.m["name"]} not found')

        for obj in objects:
            self.check_annotation(
                obj, components_map, COMPONENTS_NS, update=update)

    def check(self, update=False):
        try:
            # Collect parameters
            host = input("Host [localhost]: ") or 'localhost'  # noqa
            username = input("Username [demo]: ") or 'demo'
            password = getpass("Password: ")

            # Connect to the server
            gateway = connect(host, username, password)
            
            self.check_study(gateway, update=update)
        finally:
            gateway.close()


def main(argv):

    parser = ArgumentParser()
    parser.add_argument("studyfile", help="Study file to parse", nargs='+')
    parser.add_argument("--strict", action="store_true",
                        help="Fail if unknown keys are detected")
    parser.add_argument("--inspect", action="store_true",
                        help="Inspect the internals of the study directory")
    parser.add_argument("--report", action="store_true",
                        help="Create a report of the generated objects")
    parser.add_argument(
        '--verbose', '-v', action='count', default=0,
        help='Increase the command verbosity')
    parser.add_argument(
        '--quiet', '-q', action='count', default=0,
        help='Decrease the command verbosity')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true",
                       help="Check the study annotations on IDR")
    group.add_argument("--set", action="store_true",
                       help="Set the study annotations on IDR")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.WARN - 10 * args.verbose + 10 * args.quiet)
    log = logging.getLogger("pyidr.study_parser")

    for s in args.studyfile:
        p = StudyParser(s)
        unknown = []
        for idx, line in enumerate(p._study_lines_used):
            if not line:
                line = p._study_lines[idx].strip()
                if line and \
                        not line.startswith('#') and \
                        not line.startswith('"'):
                    key = line.split("\t")[0]
                    if args.strict:
                        unknown.append(key)
                    else:
                        log.warning("Unknown key: %s", key)
        if unknown:
            print("Found %s unknown keys:" % len(unknown))
            raise Exception("\n".join(unknown))
        d = Formatter(p, inspect=args.inspect)

        if args.report:
            print(str(d))

        if args.check or args.set:
            d.check(update=args.set)
    return p


if __name__ == "__main__":
    parser = main(sys.argv[1:])
