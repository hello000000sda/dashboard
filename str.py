import streamlit as st
import pandas as pd
import os, io
from datetime import date
import matplotlib.pyplot as plt
import altair as alt

FILE="mom_data.csv"

# ---------- LOAD SAFE ----------
if os.path.exists(FILE) and os.path.getsize(FILE)>0:
    df=pd.read_csv(FILE)
else:
    df=pd.DataFrame(columns=[
        "Meeting","Description","Date","Action","Depend On","Owner","Deadline","Status"
    ])

st.set_page_config(layout="wide")

st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
    }

    [data-testid="metric-container"] {
        background-color: #111827;
        padding: 15px;
        border-radius: 12px;
        color: white;
    }

    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] label {
        color: #60a5fa !important;  
        font-weight: 600;
    }
            
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        font-size: 20px !important;
        font-weight: 600 !important;
    }

    /* ===== Sidebar Title "Menu" ===== */
    section[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] {
        font-size: 18px !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] .stRadio > div {
        color: #ffffff !important;
    }

    button[data-testid="baseButton-save_btn"] {
        background-color: #46609b !important;
        color: black !important;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
    }
    button[data-testid="baseButton-save_btn"]:hover {
        background-color: #354a7a !important;
    }        

    h1, h2, h3 {
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True
)

st.title("MOM Management System")

menu=st.sidebar.radio("Menu",["Add MOM","Dashboard"])

# =========================================================
# ADD MOM
# =========================================================

if menu=="Add MOM":

    st.header("Create Meeting")

    meeting=st.text_input("Meeting name")
    description=st.text_area("Meeting description")
    mdate=st.date_input("Meeting date",value=date.today())

    st.subheader("Action items")

    if "rows" not in st.session_state:
        st.session_state.rows=1

    # add row button
    if st.button("➕ Add another action"):
        st.session_state.rows+=1

    actions=[]

    for i in range(st.session_state.rows):

        st.markdown(f"**Action {i+1}**")

        c1,c2,c3,c4=st.columns([4,2,2,1])

        action=c1.text_input("Action",key=f"a{i}")
        owner=c2.text_input("Owner",key=f"o{i}")
        deadline=c3.date_input("Deadline",key=f"d{i}")
        priority = c4.selectbox("Priority",["Low", "Medium", "High"],key=f"p{i}")

        actions.append((action,owner,deadline,priority))

    if st.button("💾 Save Meeting", key="save_btn", use_container_width=True):

        new_rows=[]

        for action,owner,deadline,priority in enumerate(actions):

            if i == 0:
                depends = ""
            else:
                depends = actions[i-1][0]    
                
            if action!="":
                new_rows.append({
                    "Meeting":meeting,
                    "Date":str(mdate),
                    "Description":description,
                    "Depend On":depends,
                    "Action":action,
                    "Owner":owner,
                    "Status":"Open",
                    "Deadline":str(deadline),
                    "Priority": priority
                })

        if new_rows:
            df2=pd.concat([df,pd.DataFrame(new_rows)],ignore_index=True)
            df2.to_csv(FILE,index=False)
            st.success("Saved!")
        else:
            st.warning("No action added")

# =========================================================
# DASHBOARD
# =========================================================

if menu=="Dashboard":

    st.header("Dashboard")

    if os.path.exists(FILE):

        df=pd.read_csv(FILE)
        df["Deadline"]=pd.to_datetime(df["Deadline"],errors="coerce").dt.date

        # ---------- FILTER ----------
        c1,c2,c3,c4=st.columns(4)

        meet_filter=c1.text_input("Search meeting")
        owner_filter=c2.text_input("Search owner")
        status_filter=c3.selectbox("Status",["All","Open","In Progress","Done","Overdue","Due in 3 Days"])
        priority_filter=c4.selectbox("Priority",["All","Low","Medium","High"])

        if meet_filter:
            df=df[df["Meeting"].str.contains(meet_filter,case=False,na=False)]

        if owner_filter:
            df=df[df["Owner"].str.contains(owner_filter,case=False,na=False)]

        today = pd.Timestamp.today().date()

        if status_filter == "Open":
            df = df[df["Status"]=="Open"]

        elif status_filter == "In Progress":
            df = df[df["Status"]=="In Progress"]

        elif status_filter == "Done":
            df = df[df["Status"]=="Done"]

        elif status_filter == "Overdue":
            df = df[(df["Deadline"] < today) & (df["Status"]!="Done")]

        elif status_filter == "Due in 3 Days":
            df = df[
                (df["Deadline"] >= today) &
                (df["Deadline"] <= today + pd.Timedelta(days=3)) &
                (df["Status"]!="Done")
            ]
        if priority_filter != "All":
            df = df[df["Priority"]==priority_filter]
        
        new_order = [
            "Meeting",
            "Date",
            "Description",
            "Action",
            "Depend On",
            "Owner",
            "Status",
            "Deadline",
            "Priority"
        ]

        df = df[new_order]

        column_setting = {
            "Meeting": st.column_config.TextColumn(width="medium"),
            "Date": st.column_config.TextColumn(width="small"),
            "Description": st.column_config.TextColumn(width="large"),
            "Action": st.column_config.TextColumn(width="large"),
            "Depend On": st.column_config.TextColumn(width="medium"),
            "Owner": st.column_config.TextColumn(width="medium"),
            "Status": st.column_config.SelectboxColumn(
                options=["Open","In Progress","Done"],
                width="medium"
            ),
            "Deadline": st.column_config.DateColumn(
                "Deadline",
                format="YYYY-MM-DD",
                width="small"
            ),
            "Priority": st.column_config.SelectboxColumn(
                options=["Low","Medium","High"],
                width="small"
            )
        }

        # ---------- EDIT STATUS ----------
        st.subheader("Update Status")

        edited=st.data_editor(
            df,
            use_container_width=True,
            column_config=column_setting
        )

        if st.button("SAVE STATUS"):
            edited.to_csv(FILE,index=False)
            st.success("Updated")

        # ---------- HIGHLIGHT OVERDUE ----------
        st.subheader("Table view")

        today=pd.Timestamp.today().date()
        def highlight_cells(row):

            today = pd.Timestamp.today().date()

            styles = {}

            # ===== DEADLINE =====
            if pd.notna(row["Deadline"]) and row["Status"] != "Done":
                days_left = (row["Deadline"] - today).days

                if days_left < 0:
                    styles["Deadline"] = "background-color:#ff4d4d; color:white;"
                elif 0 <= days_left <= 3:
                    styles["Deadline"] = "background-color:#fff176;"

            # ===== PRIORITY =====
            if row["Priority"] == "High":
                styles["Priority"] = "background-color:#ff4d4d; color:white;"
            elif row["Priority"] == "Medium":
                styles["Priority"] = "background-color:#fff176;"

            if pd.notna(row["Depend On"]) and row["Depend On"]!="":
                styles["Depend On"] = "background-color:#dbeafe;"

            return pd.Series(styles)

        st.dataframe(
            edited.style
                .apply(highlight_cells, axis=1)
                .set_properties(
                    subset=["Description","Action"],
                    **{'white-space': 'pre-wrap'}
                )
                .set_properties(**{
                    'border-radius': '12px'
                }),
            use_container_width=True,
            column_config=column_setting
        )
        

        # ---------- METRICS ----------
        st.divider()
        st.subheader("Summary")

        total = len(df)
        done = (df["Status"]=="Done").sum()
        open_task = (df["Status"]=="Open").sum()
        in_progress = (df["Status"]=="In Progress").sum()
        overdue = ((df["Deadline"] < pd.Timestamp.today().date()) & (df["Status"]!="Done")).sum()

        percent = int((done/total)*100) if total>0 else 0

        c1,c2,c3,c4,c5 = st.columns(5)

        def card(col, title, value, color):
            col.markdown(f"""
                <div style="
                    background:{color};
                    padding:20px;
                    border-radius:12px;
                    color:white;
                    text-align:center;
                ">
                    <h4>{title}</h4>
                    <h2>{value}</h2>
                </div>
            """, unsafe_allow_html=True
            )

        card(c1, "Total", total, "#1e40af")
        card(c2, "Open", open_task, "#f59e0b")
        card(c3, "In Progress", in_progress, "#3b82f6")
        card(c4, "Done", done, "#22c55e")
        card(c5, "Overdue", overdue, "#ff4d4d")

        st.progress(percent/100)
        st.caption(f"Completion Rate: {percent}%")

        # ---------- CHART ----------
        g1,g2,g3,g4 = st.columns([1,1,1,1])
        with g1:
            st.subheader("Status Overview")

            status_order = ["Open", "In Progress", "Done"]

            status_counts = (
                df["Status"]
                .value_counts()
                .reindex(status_order, fill_value=0)
            )

            fig, ax = plt.subplots(figsize=(5, 5), facecolor="none")

            colors = ["#f59e0b", "#3b82f6", "#22c55e"]

            wedges, texts, autotexts = ax.pie(
                status_counts,
                startangle=90,
                colors=colors,
                labels=status_counts.index,
                wedgeprops=dict(width=0.40, edgecolor="white"),
                autopct="%1.0f%%",
                pctdistance=0.8
            )

            ax.text(
                0,0,
                f"{status_counts.sum()}\nTasks",
                ha="center",
                va="center",
                fontsize=16,
                weight="bold"
            )

            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_weight("bold")

            ax.axis("equal")
            st.pyplot(fig)

        with g2:
            st.subheader("Top 5 Owner Workload")

            owner_count = (
                df["Owner"]
                .value_counts()
                .sort_values(ascending=False)
                .head(5)  
            )

            owner_df = owner_count.reset_index()
            owner_df.columns = ["Owner", "Tasks"]

            chart = (
                alt.Chart(owner_df)
                .mark_bar(
                    cornerRadiusTopLeft=6,
                    cornerRadiusTopRight=6
                )
                .encode(
                    x=alt.X("Owner:N", sort="-y"),
                    y=alt.Y("Tasks:Q"),
                    color=alt.value("#46609b"),
                    tooltip=["Owner","Tasks"]
                )
                .properties(height=300)
            )

            st.altair_chart(chart, use_container_width=True)
            

        # ---------- EXPORT ----------
        st.subheader("Export Excel")

        buffer=io.BytesIO()
        edited.to_excel(buffer,index=False)
        buffer.seek(0)

        st.download_button(
            "Download Excel",
            data=buffer,
            file_name="mom.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.info("No data")