import load_env 
from get_LMP import df1

import pandas as pd
import pandas_gbq
import os
dataset = os.environ.get("WORKSPACE_CDR")

print(df1)

def cluster_lmps(df):
    df = df.sort_values("estimated_lmp").copy()

    cluster = 0
    cluster_start = df.iloc[0]["estimated_lmp"] #initialze as first (earlistest) lmp
    labels = []

    for lmp in df["estimated_lmp"]:
        if (lmp - cluster_start).days > 42: #6 weeks =42 days
            cluster += 1
            cluster_start = lmp #restart cluster

        labels.append(cluster)

    df["cluster"] = labels
    return df

#get clusters and get median of LMPs
clustered = (df1.groupby("person_id", group_keys=False)
             .apply(cluster_lmps)
             .reset_index(drop=True))

def median(x):
    # vals = x.sort_values().astype("int64")
    # return pd.to_datetime(vals.iloc[(len(vals)-1)//2])
    return pd.to_datetime(x).median()

lmp_summary = (clustered
               .groupby(["person_id", "cluster"], as_index=False)
               .agg(median_lmp=("estimated_lmp", median),
                    n_records=("estimated_lmp", "size"), #amount of codes
                    min_lmp=("estimated_lmp", "min"),
                    max_lmp=("estimated_lmp", "max")))

def lmp_score(lmps):
    lmps = pd.to_datetime(lmps).sort_values().reset_index(drop=True)
    n = len(lmps)

    # Median LMP
    med = median(lmps)

    #S1= number of obseravtions
    S1 = min(n/10, 1)

    #S2= % of observations that are within 7 days of the median
    distances = (lmps - med).dt.days.abs()
    S2 = (distances <= 7).mean()

    #S3= difference between mode and mean
    mode_val = lmps.mode().iloc[0]
    d = abs((med - mode_val).days)
    S3 = max(0, 1 - d/7)

    #S4= % of observatios thats the mode
    p = (lmps == mode_val).mean()
    S4 = p

    score = 100 * 0.25 * (S1+ S2 + S3 + S4)

    return round(score, 1)


def merge_clusters(df):
    df = df.sort_values("median_lmp").reset_index(drop=True)
    merged = []
    i = 0

    while i < len(df):
        current = df.iloc[i].copy()
        if i < len(df)-1: # check if theres another cluster after this one
            nxt = df.iloc[i+1]
            if (nxt["median_lmp"] - current["median_lmp"]).days <= 56:
                all_rows = pd.concat([clustered[(clustered.person_id == current.person_id) &
                                       (clustered.cluster == current.cluster)],
                                       clustered[(clustered.person_id == nxt.person_id) &
                                       (clustered.cluster == nxt.cluster)]]) #retrieve lmp estimates from both clusters
                all_dates = all_rows["estimated_lmp"]
                last_record = all_rows.sort_values("condition_start_date").iloc[-1]
                merged.append({
                    "person_id": current.person_id,
                    "episode_id": len(merged),
                    "median_lmp": median(all_dates),
                    "score": lmp_score(all_dates),
                    # "n_clusters": 2,
                    "n_records": len(all_dates),
                    "min_lmp": all_dates.min(),
                    "max_lmp": all_dates.max(),
                    "last_zcode": last_record["concept_code"],
                    "last_zcode_date": last_record["condition_start_date"]})
                i += 2 #skip next cluster (merged)
                continue
                
        # keep cluster as its own episode
        all_rows = clustered[(clustered.person_id == current.person_id) &
                    (clustered.cluster == current.cluster)]
        all_dates = all_rows["estimated_lmp"]
        last_record = all_rows.sort_values("condition_start_date").iloc[-1]
        
        merged.append({
            "person_id": current.person_id,
            "episode_id": len(merged),
            "median_lmp": current.median_lmp,
            "score": lmp_score(all_dates),
            # "n_clusters": 1,
            "n_records": current.n_records,
            "min_lmp": current.min_lmp,
            "max_lmp": current.max_lmp,
            "last_zcode": last_record["concept_code"],
            "last_zcode_date": last_record["condition_start_date"]})
        i += 1

    return pd.DataFrame(merged)

#apply for each person
final_episodes = (lmp_summary.groupby("person_id", group_keys=False)
                  .apply(merge_clusters)
                  .reset_index(drop=True))
