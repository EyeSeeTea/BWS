# Database management guide [WIP]

This guide provides instructions on how to update entries in the database, and the list of available commands along with a code description.

## Main (update entries)

Command for updating PDB Entries (app/api/management/commands/update_entries_from_dir.py)
1. The entries are updating by reading the data from a path: get_structures_from_path()
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