**Setup**
- Log in to the All of Us Researcher Workbench. Create a new workspace (or use an existing workspace). From Resources, select data from catalog with access to the CDR v8 dataset.
- Create a cohort in the Resources tab of your workspace. The cohort for this project is all people assigned female at brith (AFAB)
- In apps, create a new Jupyter instance. Upload all files from this repository. (Z3A_Algorithm.ipynb, load_env.py, get_LMPs.py, get_Episodes.py)

**Running the Algorithm**

Run the master notebook: Z3A_Algorithm.ipynb

*May need to run !conda install pandas pandas-gbq os  

The notebook will:
- Load the required Python environment and import required packages.
- Query Z3A gestational age diagnosis codes from the All of Us dataset.
- Estimate last menstrual period (LMP) dates.
- Cluster LMP estimates into pregnancy episodes.
- Generate a pregnancy episode table with confidence scores and summary information.

**Exporting Results**
If you would like to save the pregnancy episodes as a CSV file, uncomment the export cell (the second cell of the notebook) and run it after the algorithm finishes.

**Last Updated**
June 13, 2026
Python: 3.10.19 | pandas: 2.3.2 | pandas-gbq: 0.27.0
