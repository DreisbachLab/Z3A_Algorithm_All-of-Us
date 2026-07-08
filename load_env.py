import json
import subprocess
import os
import re

# --- Extract variables directly into os.environ ---
workspace = json.loads(subprocess.run(
    ["wb", "workspace", "describe", "--format=json"],
    capture_output=True, text=True, check=True
).stdout)

os.environ["GOOGLE_CLOUD_PROJECT"] = workspace["googleProjectId"]

resources = json.loads(subprocess.run(
    ["wb", "resource", "list", "--format=json"],
    capture_output=True, text=True, check=True
).stdout)

os.environ["WORKSPACE_CDR"] = ""

# --- Step 3: Extract workspace resources ---
for r in resources:

    # 1. BUCKET LOGIC
    if r["resourceType"] == "GCS_BUCKET":
        print(f"Found bucket: id={r['id']}, bucketName={r['bucketName']}")

        if "temporary-workspace-bucket" in r["id"]:
            os.environ["WORKSPACE_TEMP_BUCKET"] = f"gs://{r['bucketName']}"

        elif "workspace-bucket" in r["id"]:
            os.environ["WORKSPACE_BUCKET"] = f"gs://{r['bucketName']}"

    # 2. BQ DATASET LOGIC  ← SAME LEVEL as bucket logic
    elif r["resourceType"] in ["BQ_DATASET", "BIGQUERY_DATASET"]:

        if os.environ.get("WORKSPACE_CDR", "") == "":

            dataset_id = r["datasetId"]

            # Match real All of Us CDR pattern like C2024Q3R8
            if re.match(r"^C\d{4}Q\d+R\d+$", dataset_id):

                os.environ["WORKSPACE_CDR"] = f"{r['projectId']}.{dataset_id}"

                print(f"Successfully set WORKSPACE_CDR to: {os.environ['WORKSPACE_CDR']}")


# --- Print what we got ---
print("\nVariables extracted:")
for var in ["GOOGLE_CLOUD_PROJECT", "WORKSPACE_BUCKET", 
            "WORKSPACE_TEMP_BUCKET", "WORKSPACE_CDR"]:
    value = os.environ.get(var)
    print(f"{var}: {value if value else 'NOT FOUND'}")


# --- Save to .bashrc (no dictionary needed!) ---
bashrc_path = os.path.expanduser("~/.bashrc")

# Check if .bashrc exists, create it if not
if not os.path.exists(bashrc_path):
    print(f"Creating {bashrc_path}...")
    with open(bashrc_path, "w") as f:
        f.write("# Created by Verily setup script\n")

# Now continue with reading/appending
# Simple approach: just append (will create duplicates if run multiple times)
with open(bashrc_path, "a") as f:
    f.write("\n# Verily Workbench variables\n")
    for var in ["GOOGLE_CLOUD_PROJECT", "WORKSPACE_BUCKET", 
                "WORKSPACE_TEMP_BUCKET", "WORKSPACE_CDR"]:
        value = os.environ.get(var)
        if value:
            f.write(f'export {var}="{value}"\n')

print(f"\n Saved to {bashrc_path}")

for r in resources:
    print(r["id"], r["resourceType"])
    if r["resourceType"] == "GCS_BUCKET" and "workspace-bucket" in r["id"]:
        os.environ["WORKSPACE_BUCKET"] = f"gs://{r['bucketName']}"
    elif r["resourceType"] == "GCS_BUCKET" and "temporary" in r["id"]:
        os.environ["WORKSPACE_TEMP_BUCKET"] = f"gs://{r['bucketName']}"

# In your notebook, just run this:
with open(os.path.expanduser("~/.bashrc"), 'r') as f:
    for line in f:
        if line.strip().startswith('export '):
            parts = line.strip().replace('export ', '').split('=', 1)
            if len(parts) == 2:
                var_name = parts[0].strip()
                var_value = parts[1].strip().strip("'\"")
                
                # SKIP PATH completely!
                if var_name == 'PATH':
                    continue  # Skip this line
                    
                os.environ[var_name] = var_value

# Now use them
print(f"GOOGLE_CLOUD_PROJECT = {os.environ.get('GOOGLE_CLOUD_PROJECT')}")
print(f"WORKSPACE_BUCKET = {os.environ.get('WORKSPACE_BUCKET')}")
