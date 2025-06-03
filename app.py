import streamlit as st
import pandas as pd
import requests
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Profile Analysis Dashboard", layout="wide")
st.title("Profile Analysis Dashboard")
st.markdown("Upload your spreadsheet to analyze GitHub profiles using an API.")

uploaded_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith("xlsx") else pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Failed to read file: {str(e)}")
        st.stop()

    required_cols = ["First Name", "Last Name", "This is my GitHub ID"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Missing columns: {', '.join(missing_cols)}")
        st.stop()

    df = df.rename(columns={"This is my GitHub ID": "GitHub ID"})
    df = df[["First Name", "Last Name", "GitHub ID"]].copy()
    df.fillna("", inplace=True)

    st.success(f"Loaded {len(df)} rows.")
    st.dataframe(df, use_container_width=True)

    tabs = st.tabs(["Summary", "GitHub"])

    results = []
    errors = []
    progress_bar = st.progress(0)
    total_rows = len(df)

    try:
        for i, row in df.iterrows():
            github_id = row["GitHub ID"]
            user_key = f"{row['First Name']}_{row['Last Name']}"

            try:
                res = requests.post(
                    "http://127.0.0.1:8000/scrape-github",
                    json={"github_id": github_id}
                )
                github_result = res.json()

                if github_result.get("error"):
                    errors.append(f"Row {i+1} ({user_key}): {github_result['error']}")

                results.append({"github": github_result})
            except Exception as e:
                errors.append(f"Row {i+1} ({user_key}): Request error - {str(e)}")
                results.append({"github": {"error": "Request error", "count": 0, "repos": []}})

            progress_bar.progress((i + 1) / total_rows)
    finally:
        pass

    with tabs[0]:
        st.header("Summary")
        valid_github = sum(1 for r in results if not r["github"].get("error"))
        summary_data = {
            "Total Users": len(df),
            "Valid GitHub IDs": valid_github,
            "Average GitHub Repos": round(np.mean([r["github"]["count"] for r in results if not r["github"].get("error")] or [0]), 2)
        }
        st.dataframe(pd.DataFrame([summary_data]), use_container_width=True)
        if errors:
            with st.expander("View Errors"):
                st.write("\n".join(errors))

    with tabs[1]:
        for i, row in df.iterrows():
            user_key = f"{row['First Name']} {row['Last Name']}"
            st.subheader(f"{user_key} (GitHub: {row['GitHub ID'] or 'None'})")
            result = results[i]["github"]
            if result.get("error"):
                st.warning(result["error"])
            else:
                st.metric("Total Repositories", result["count"])
                if result["repos"]:
                    st.dataframe(pd.DataFrame(result["repos"]), use_container_width=True)
                    langs = [repo["language"] for repo in result["repos"] if repo["language"] != "Unknown"]
                    if langs:
                        lang_counts = pd.Series(langs).value_counts()
                        fig = px.bar(x=lang_counts.index, y=lang_counts.values, labels={"x": "Language", "y": "Count"}, title="Repository Languages")
                        st.plotly_chart(fig, use_container_width=True, key=f"github_chart_{i}")
                else:
                    st.info("No repositories found.")

    results_df = pd.DataFrame([
        {
            "First Name": row["First Name"],
            "Last Name": row["Last Name"],
            "GitHub ID": row["GitHub ID"] or "None",
            "GitHub Repos": results[i]["github"]["count"] if not results[i]["github"].get("error") else results[i]["github"].get("error")
        }
        for i, row in df.iterrows()
    ])
    csv = results_df.to_csv(index=False)
    st.download_button("Download Results", csv, "profile_results.csv", "text/csv", use_container_width=True)