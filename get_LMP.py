import load_env
import os
dataset = os.environ.get("WORKSPACE_CDR")

import pandas as pd
import pandas_gbq

query = f"""
WITH z3a_mapping AS (
    SELECT
        icd.concept_code,
        std.concept_id AS standard_concept_id
    FROM `{dataset}.concept` icd
    JOIN `{dataset}.concept_relationship` cr
        ON icd.concept_id = cr.concept_id_1
    JOIN `{dataset}.concept` std
        ON cr.concept_id_2 = std.concept_id
    WHERE icd.concept_code LIKE 'Z3A.%'
      AND cr.relationship_id = 'Maps to'
)

SELECT
    co.person_id,
    co.condition_start_date,
    z.concept_code
FROM `{dataset}.condition_occurrence` co
JOIN z3a_mapping z
    ON co.condition_concept_id = z.standard_concept_id
"""

df1 = pandas_gbq.read_gbq(query)
df1 = df1.sort_values(["person_id", "condition_start_date", "concept_code"])

def z3a_to_weeks(code):
    if code in {"Z3A.00", "Z3A.0", "Z3A.1", "Z3A.2","Z3A.3","Z3A.4","Z3A.49"}:
        return None
    if code == "Z3A.01":
        return 7
    return int(code.split(".")[1])

df1["weeks"] = df1["concept_code"].apply(z3a_to_weeks)

df1 = df1[df1["weeks"].notna()]

df1 = df1.drop_duplicates(
    subset=["person_id", "condition_start_date", "concept_code", "weeks"]
)

#estimate LMP using formula: start-weeks of gestation
df1["estimated_lmp"] = (
    pd.to_datetime(df1["condition_start_date"])
    - pd.to_timedelta(df1["weeks"] * 7, unit="D")
)

#sort by person to see range in LMP
df1 = df1.sort_values(["person_id", "condition_start_date", "concept_code"])

df1




