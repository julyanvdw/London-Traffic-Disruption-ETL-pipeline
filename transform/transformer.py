"""
Julyan van der Westhuizen
16/07/25

This script performs the ingestion of raw, collected data files: 
1) Each snapshot contians 0..n traffic disruptions
2) Data then undergoes validation and cleaning by parisng the JSON data with pydantic models defined in tims_models.py
"""

from transform.tims_models import Disruption
from datalake_manager import LakeManager
from pipeline_log_manager import shared_logger


def ingest_tims_data():
    
    processed_data = []
    manager = LakeManager()
    files_data = manager.read_TIMS_raw_snapshot()

    fields_stripped_count = 0

    # Set to OK (code 0) by default
    shared_logger.last_run_info["Transform-status"] = 0

    # note: files_data represnets data in the format [file_in_raw_tims_dir][data_item_for_that_file]
    for data in files_data:
        # data represetns a collection of data items (disruptions)
        for d in data:
            # try auto-converting by parsing with pydantic
            try: 
                disruption = Disruption(**d)
                processed_data.append(disruption)

                # update metric
                fields_stripped_count += len(d) - len(Disruption.model_fields)

            except Exception as e:
                shared_logger.log_warning(f"Could not parse data item in snapshot: {e}")
                shared_logger.last_run_info["Transform-status"] = 1
            
    # remove possible duplicates in the data
    seen = {}
    for disruption in processed_data:
        if disruption.tims_id not in seen: 
            seen[disruption.tims_id] = disruption

    deduplicated_data = list(seen.values())

    shared_logger.last_run_info["Data-transformed"] = str(len(deduplicated_data))
    shared_logger.last_run_info["Fields-stripped"] = str(fields_stripped_count)

    manager.write_TIMS_transformed_snapshot(deduplicated_data)
    shared_logger.log("Successfully wrote transformed snapshot.")


def ingest():
    ingest_tims_data()

    # FUTURE WORK: can add other ingestion streams here. We can also do data-integration here. 

if __name__ == "__main__":
    ingest()

   