# Database management guide [WIP]

This guide provides instructions on how to update entries in the database, and the list of available commands along with a code description.

## Main (update entries from dir)

Command for updating PDB Entries (app/api/management/commands/update_entries_from_dir.py)
1. Calls directly get_structures_from_path(path, start), along with the indicated folder, and an optional start index
2. It retrieves all the mmcif files on that path: get_mmcif_files(path)
3. For each file, optionally it can start from certain index filename, it will convert mmcif to dictionary: convert_mmcif_to_dictionary(path, filename)
4. For each dictionary, it will read and search for the properties: read_mmcif_file(mmCifDict)
    - Gets PDB Entry ID -> After that it updates the PDB entry: updatePdbEntrymmCifFile -> updatePdbentry
    - Finds the associated EM volume -> After that it updates the EMDB entry: updateEmdbEntrymmCifFile -> updateEmdbEntry
    - If there is EMDB ID, it updates the HybridModel (the table relationship between PDB and EMDB entries): updateHybridModel
    - Retrieves the associated entities (except ligands)
        - UniProt, retrieves and updates: updateUniProtEntry
        - Organism, retrieves and updates: updateOrganism
        - ModelEntity (PolymerEntity), retrieves and updates: updateEntitymmCifFile
        - PDBToEntity (PDB-Polymer), retrieves and updates: updatePdbToEntity
        - NMRTargetToModelEntity, retrieves and updates: updateNMRTargetToModelEntity
    - Retrieves the ligands
        - Get "branched" ligands (not operative right now, the code is commented): getPdbToLigandListmmCifFile("branched") -> updatePdbToLigand
        - Get non-polymer ligands: getPdbToLigandListmmCifFile("non-polymer") -> updatePdbToLigand
    - Fetches for RefinedModel (PDB-Redo): getRefinedModelPDBRedo -> updateRefinedModel
    - If EMDB ID, fetches for RefinedModel (CERES): getRefinedModelCeres -> updateRefinedModel
    - NOTE: (Isolde RefinedModel not here, but on update_isolde_refinements function is alone by himself)
    - NOTE: (Should check also for Refmac?)
    - Get Authors (submission authors): getPdbEntryAuthors -> updateAuthor
    - Retrieves PDB Entry details: (updatePdbEntryDetails <- getSampleDetails <- updateSampleEntity)
    - Retrieves Publications (DB Citations): getPublications -> (updatePublication && getCitationAuthors -> updatePublicationAuthor)
    - And sets Entry details .refdoc with the publications

## Init base tables

Command to setup some base tables that need/may contain fixed data (app/api/management/commands/init_base_tables.py)
1. Calls directly init_base_tables(), which initializes some base tables:
    - RefinedModelSources - initRefinedModelSources()
    - RefinedModelMethods - initRefinedModelMethods()
    - Topics - initTopics()
2. This tables are hardcoded entities for description purposes.

## Init NMR targets

Command to setup some base tables that need/may contain fixed data (app/api/management/commands/init_nmr_targets.py)
1. Calls directly init_nmr_targets(), which calls again initNMRTargets().
2. From the data of a hardcoded array "nmrentity_list" it iteratees:
    - Getting or creating a UniProt by target's "uniprot_acc": getOrCreateUniProtEntry
    - Adding the nmr entries: updateNMRTarget

## Init UniProt entries

Command creating UniProt entries for each of the SARS-CoV-2 proteins in UniProtEntry table. (app/api/management/commands/init_uniprot_entry.py)
- Requires "CSV file path, i.e.: /data/SARS-CoV-2/UniProtEntry_covid19-proteome.csv"

1. Calls directly init_uniprot_entry(filepath), where filepath is the csv given
2. For each csv row, it creates or updates the UniProt entries: updateUniProtEntry

## Update PDB Redo

Update PDB Redo entries (RefinedModels) (app/api/management/commands/update_pdb_redo.py)
1. Retrieves the list of PDB entries
2. For each PDB ID, it fetches into [URL_PDB_REDO]/db/[pdb_id]/pdbe.json (with a 1 second cooldown in between requests)
    - If HTTP 200, means it exists
    - Else, means it doesn't exists
3. Saves the result (the 'success' ones, and the 'not found' ones), into a json on /data/pdb_redo_entries/ along with the filename being `pdb_redo_{timestamp}.json`
4. Retrieves the actual RefinedModels
5. For the found ones that aren't already on RefinedModels, it will create the entries.
6. For the not found ones that are on RefinedModels, it will delete those entries.

## Update Isolde

--

## Update NMR binding

--

## Update Assay dirs from GitHub

--

## Update DB from HCS Assay

--