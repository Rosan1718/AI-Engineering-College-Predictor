import streamlit as st
import pandas as pd
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Engineering College Predictor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# DATA FILE
# =========================================================

DATA_FILE = "data/cutoff_2025.csv"

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    data = pd.read_csv(DATA_FILE)

    data.columns = (
        data.columns
        .astype(str)
        .str.strip()
    )

    for column in data.columns:

        if data[column].dtype == "object":

            data[column] = (
                data[column]
                .astype(str)
                .str.strip()
            )

    return data


try:

    df = load_data()

except Exception as error:

    st.error("❌ Dataset could not be loaded.")

    st.code(str(error))

    st.info(
        "Make sure your dataset is located at:\n"
        "data/cutoff_2025.csv"
    )

    st.stop()

# =========================================================
# REQUIRED COLUMNS
# =========================================================

required_columns = [
    "College Name",
    "Branch",
    "District"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    st.error(
        "❌ Missing columns: "
        + ", ".join(missing_columns)
    )

    st.stop()

# =========================================================
# OPTIONS
# =========================================================

departments = sorted(
    df["Branch"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
    .tolist()
)

districts = sorted(
    df["District"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
    .tolist()
)

communities = [
    "OC",
    "BC",
    "BCM",
    "MBC",
    "SC",
    "SCA",
    "ST"
]

# =========================================================
# SESSION STATE
# =========================================================

if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None

if "student_name" not in st.session_state:
    st.session_state.student_name = ""

if "student_cutoff" not in st.session_state:
    st.session_state.student_cutoff = 0.0

if "student_community" not in st.session_state:
    st.session_state.student_community = "OC"

if "student_department" not in st.session_state:
    st.session_state.student_department = "All Departments"

if "student_district" not in st.session_state:
    st.session_state.student_district = "All Districts"

# =========================================================
# PROFESSIONAL LIGHT DASHBOARD CSS
# =========================================================

st.markdown(
    """
    <style>
    .stApp { background-color: #f7f9fc; }
    .main .block-container { max-width: 1400px; padding-top: 1.5rem; padding-bottom: 3rem; }
    .dashboard-header { background:#fff; padding:30px 34px; border-radius:20px; border:1px solid #e5eaf0; margin-bottom:25px; box-shadow:0 5px 20px rgba(0,0,0,.04); }
    .dashboard-title { font-size:36px; font-weight:800; color:#172033; margin:0; }
    .dashboard-subtitle { color:#667085; font-size:15px; margin-top:8px; }
    .section-title { font-size:24px; font-weight:750; color:#172033; margin-top:28px; margin-bottom:16px; }
    .metric-card { background:#fff; border:1px solid #e5eaf0; border-radius:16px; padding:20px; min-height:105px; box-shadow:0 4px 14px rgba(0,0,0,.035); }
    .best-card { background:#fff; border:1px solid #dce5f1; border-radius:22px; padding:28px; margin-bottom:25px; box-shadow:0 8px 28px rgba(37,99,235,.08); }
    .best-badge { display:inline-block; padding:6px 12px; border-radius:20px; background:#eff6ff; color:#2563eb; font-size:12px; font-weight:800; letter-spacing:.5px; }
    .best-college { font-size:27px; font-weight:800; color:#172033; margin-top:13px; line-height:1.3; }
    .best-info { color:#667085; font-size:14px; margin-top:9px; }
    .best-score-container { margin-top:20px; padding:15px; border-radius:14px; background:#f5f8ff; text-align:center; }
    .best-score { color:#2563eb; font-size:38px; font-weight:850; }
    .best-score-label { color:#667085; font-size:11px; font-weight:600; }
    .college-card { background:#fff; border:1px solid #e5eaf0; border-radius:18px; padding:22px; min-height:270px; margin-bottom:18px; box-shadow:0 4px 15px rgba(0,0,0,.035); }
    .college-rank { color:#667085; font-size:11px; font-weight:800; letter-spacing:.8px; text-transform:uppercase; }
    .college-name { color:#172033; font-size:19px; font-weight:750; line-height:1.35; margin-top:8px; margin-bottom:15px; }
    .college-info { color:#667085; font-size:13px; margin:8px 0; line-height:1.45; }
    .score-box { background:#f5f8ff; border-radius:12px; padding:11px; margin-top:16px; text-align:center; }
    .score-number { color:#2563eb; font-size:25px; font-weight:800; }
    .score-label { color:#667085; font-size:10px; font-weight:600; margin-top:2px; }
    .status-safe,.status-high,.status-moderate,.status-borderline,.status-low { display:inline-block; padding:5px 11px; border-radius:20px; font-size:11px; font-weight:750; }
    .status-safe { background:#ecfdf3; color:#15803d; } .status-high { background:#f0fdf4; color:#16a34a; }
    .status-moderate { background:#fffbeb; color:#b45309; } .status-borderline { background:#fff7ed; color:#c2410c; } .status-low { background:#fef2f2; color:#dc2626; }
    section[data-testid="stSidebar"] { background:#fff; border-right:1px solid #e5eaf0; }
    .stButton > button { border-radius:10px; font-weight:650; min-height:43px; }
    div[data-baseweb="select"] > div, div[data-testid="stTextInput"] input { border-radius:10px; }
    div[data-testid="stDataFrame"] { border-radius:14px; overflow:hidden; }
    @media (max-width:768px) { .dashboard-title{font-size:27px;} .best-college{font-size:21px;} .college-name{font-size:17px;} }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# PDF HELPERS
# =========================================================

def pdf_chance(chance):

    chance = str(chance)

    if "Safe" in chance:
        return "SAFE"

    if "High Chance" in chance:
        return "HIGH CHANCE"

    if "Moderate" in chance:
        return "MODERATE"

    if "Borderline" in chance:
        return "BORDERLINE"

    return "LOW CHANCE"


# =========================================================
# CREATE PDF REPORT
# =========================================================

def create_pdf_report(
    student_name,
    cutoff,
    community,
    department,
    district,
    result
):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    # -----------------------------------------------------
    # PDF STYLES
    # -----------------------------------------------------

    title_style = ParagraphStyle(
        "PDFTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=23,
        alignment=TA_CENTER,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        "PDFSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
        spaceAfter=15
    )

    heading_style = ParagraphStyle(
        "PDFHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        spaceBefore=8,
        spaceAfter=9
    )

    table_text_style = ParagraphStyle(
        "PDFTableText",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.2,
        leading=9,
        wordWrap="CJK"
    )

    table_header_style = ParagraphStyle(
        "PDFTableHeader",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=7.2,
        leading=9,
        wordWrap="CJK"
    )

    small_style = ParagraphStyle(
        "PDFSmall",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=11
    )

    elements = []

    # =====================================================
    # TITLE
    # =====================================================

    elements.append(
        Paragraph(
            "AI Engineering College Predictor",
            title_style
        )
    )

    elements.append(
        Paragraph(
            "2025 TNEA College Prediction Report",
            subtitle_style
        )
    )

    # =====================================================
    # STUDENT DETAILS
    # =====================================================

    elements.append(
        Paragraph(
            "Student Details",
            heading_style
        )
    )

    student_data = [

        [
            Paragraph(
                "Student Name",
                table_header_style
            ),
            Paragraph(
                str(student_name),
                table_text_style
            )
        ],

        [
            Paragraph(
                "Cutoff Mark",
                table_header_style
            ),
            Paragraph(
                f"{cutoff:.1f}",
                table_text_style
            )
        ],

        [
            Paragraph(
                "Community",
                table_header_style
            ),
            Paragraph(
                str(community),
                table_text_style
            )
        ],

        [
            Paragraph(
                "Department",
                table_header_style
            ),
            Paragraph(
                str(department),
                table_text_style
            )
        ],

        [
            Paragraph(
                "Preferred District",
                table_header_style
            ),
            Paragraph(
                str(district),
                table_text_style
            )
        ]
    ]

    student_table = Table(
        student_data,
        colWidths=[
            150,
            365
        ]
    )

    student_table.setStyle(
        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    elements.append(student_table)

    elements.append(
        Spacer(1, 18)
    )

    # =====================================================
    # BEST RECOMMENDATION
    # =====================================================

    if not result.empty:

        best = result.iloc[0]

        elements.append(
            Paragraph(
                "Best AI Recommendation",
                heading_style
            )
        )

        best_data = [

            [
                Paragraph(
                    "College",
                    table_header_style
                ),
                Paragraph(
                    str(best["College Name"]),
                    table_text_style
                )
            ],

            [
                Paragraph(
                    "Department",
                    table_header_style
                ),
                Paragraph(
                    str(best["Branch"]),
                    table_text_style
                )
            ],

            [
                Paragraph(
                    "District",
                    table_header_style
                ),
                Paragraph(
                    str(best["District"]),
                    table_text_style
                )
            ],

            [
                Paragraph(
                    f"2025 {community} Cutoff",
                    table_header_style
                ),
                Paragraph(
                    f"{best[community]:.1f}",
                    table_text_style
                )
            ],

            [
                Paragraph(
                    "AI Match Score",
                    table_header_style
                ),
                Paragraph(
                    f"{best['Match Score']:.1f}%",
                    table_text_style
                )
            ],

            [
                Paragraph(
                    "Prediction",
                    table_header_style
                ),
                Paragraph(
                    pdf_chance(best["Chance"]),
                    table_text_style
                )
            ]
        ]

        best_table = Table(
            best_data,
            colWidths=[
                170,
                345
            ]
        )

        best_table.setStyle(
            TableStyle([

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ])
        )

        elements.append(best_table)

        elements.append(
            Spacer(1, 18)
        )

    # =====================================================
    # TOP 10
    # =====================================================

    elements.append(
        Paragraph(
            "Top AI Recommendations",
            heading_style
        )
    )

    top10 = result.head(10)

    report_data = [

        [
            Paragraph(
                "Rank",
                table_header_style
            ),

            Paragraph(
                "College",
                table_header_style
            ),

            Paragraph(
                "Department",
                table_header_style
            ),

            Paragraph(
                "Cutoff",
                table_header_style
            ),

            Paragraph(
                "AI Score",
                table_header_style
            ),

            Paragraph(
                "Chance",
                table_header_style
            )
        ]
    ]

    for index, (_, row) in enumerate(
        top10.iterrows(),
        start=1
    ):

        college_name = str(
            row["College Name"]
        )

        branch_name = str(
            row["Branch"]
        )

        cutoff_value = (
            f"{row[community]:.1f}"
        )

        score_value = (
            f"{row['Match Score']:.1f}%"
        )

        chance_value = pdf_chance(
            row["Chance"]
        )

        report_data.append(

            [
                Paragraph(
                    str(index),
                    table_text_style
                ),

                Paragraph(
                    college_name,
                    table_text_style
                ),

                Paragraph(
                    branch_name,
                    table_text_style
                ),

                Paragraph(
                    cutoff_value,
                    table_text_style
                ),

                Paragraph(
                    score_value,
                    table_text_style
                ),

                Paragraph(
                    chance_value,
                    table_text_style
                )
            ]
        )

    report_table = Table(
        report_data,
        repeatRows=1,

        colWidths=[
            30,
            185,
            115,
            50,
            60,
            75
        ]
    )

    report_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "ALIGN",
                (0, 0),
                (0, -1),
                "CENTER"
            ),

            (
                "ALIGN",
                (3, 1),
                (4, -1),
                "CENTER"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    elements.append(report_table)

    elements.append(
        Spacer(1, 18)
    )

    # =====================================================
    # DISCLAIMER
    # =====================================================

    elements.append(
        Paragraph(
            "<b>Disclaimer:</b> This report is based on "
            "historical 2025 cutoff data and an AI-based "
            "recommendation score. It is not a guarantee "
            "of admission. Actual admission depends on "
            "the official counselling process, seat "
            "availability and applicable rules.",
            small_style
        )
    )

    # =====================================================
    # BUILD PDF
    # =====================================================

    document.build(elements)

    buffer.seek(0)

    return buffer.getvalue()


# =========================================================
# AI MATCH SCORE
# =========================================================

def calculate_match_score(
    cutoff,
    college_cutoff,
    department_selected,
    college_branch,
    district_selected,
    college_district
):

    difference = (
        cutoff -
        college_cutoff
    )

    # -----------------------------------------------------
    # CUTOFF = 70%
    # -----------------------------------------------------

    if difference >= 15:
        cutoff_score = 100

    elif difference >= 10:
        cutoff_score = 95

    elif difference >= 5:
        cutoff_score = 88

    elif difference >= 3:
        cutoff_score = 82

    elif difference >= 0:
        cutoff_score = 75

    elif difference >= -3:
        cutoff_score = 60

    elif difference >= -5:
        cutoff_score = 45

    elif difference >= -10:
        cutoff_score = 25

    else:
        cutoff_score = 10

    # -----------------------------------------------------
    # DEPARTMENT = 20%
    # -----------------------------------------------------

    if department_selected == "All Departments":

        department_score = 70

    elif (
        str(college_branch).strip().lower()
        ==
        str(department_selected).strip().lower()
    ):

        department_score = 100

    else:

        department_score = 35

    # -----------------------------------------------------
    # DISTRICT = 10%
    # -----------------------------------------------------

    if district_selected == "All Districts":

        district_score = 70

    elif (
        str(college_district).strip().lower()
        ==
        str(district_selected).strip().lower()
    ):

        district_score = 100

    else:

        district_score = 30

    # -----------------------------------------------------
    # FINAL SCORE
    # -----------------------------------------------------

    final_score = (
        cutoff_score * 0.70
        +
        department_score * 0.20
        +
        district_score * 0.10
    )

    return round(
        min(
            max(
                final_score,
                0
            ),
            100
        ),
        1
    )


# =========================================================
# PROFESSIONAL DASHBOARD HEADER
# =========================================================

st.markdown(
    """
    <div class="dashboard-header">
        <div class="dashboard-title">🎓 AI Engineering College Predictor</div>
        <div class="dashboard-subtitle">Smart engineering college recommendations using <b>2025 TNEA cutoff data</b></div>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# DATASET OVERVIEW
# =========================================================

st.markdown(
    '<div class="section-title">'
    '📊 Dataset Overview'
    '</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "🎓 Colleges",
        df["College Name"].nunique()
    )

with c2:

    st.metric(
        "📚 Departments",
        len(departments)
    )

with c3:

    st.metric(
        "📍 Districts",
        df["District"].nunique()
    )

with c4:

    st.metric(
        "📅 Data Year",
        "2025"
    )

# =========================================================
# STUDENT DETAILS
# =========================================================

st.markdown(
    '<div class="section-title">'
    '👨‍🎓 Student Details'
    '</div>',
    unsafe_allow_html=True
)

c1, c2 = st.columns(2)

with c1:

    name = st.text_input(
        "👤 Student Name",
        value=st.session_state.student_name,
        placeholder="Enter your name"
    )

with c2:

    cutoff = st.number_input(
        "📊 Cutoff Mark",
        min_value=0.0,
        max_value=200.0,
        value=float(
            st.session_state.student_cutoff
        ),
        step=0.5
    )

c3, c4 = st.columns(2)

with c3:

    community = st.selectbox(
        "👥 Community",
        communities,
        index=communities.index(
            st.session_state.student_community
        )
    )

with c4:

    district_options = [
        "All Districts"
    ] + districts

    district = st.selectbox(
        "📍 Preferred District",
        district_options,
        index=district_options.index(
            st.session_state.student_district
        )
    )

# =========================================================
# DEPARTMENT
# =========================================================

department_options = [
    "All Departments"
] + departments

department = st.selectbox(
    "🎓 Preferred Department",
    department_options,
    index=department_options.index(
        st.session_state.student_department
    )
)

st.caption(
    f"✅ {len(departments)} departments available "
    "from the 2025 dataset."
)

# =========================================================
# BUTTONS
# =========================================================

b1, b2 = st.columns(2)

with b1:

    predict = st.button(
        "🤖 GET AI RECOMMENDATIONS",
        type="primary",
        use_container_width=True
    )

with b2:

    reset = st.button(
        "🔄 RESET",
        use_container_width=True
    )

# =========================================================
# RESET
# =========================================================

if reset:

    st.session_state.prediction_result = None
    st.session_state.student_name = ""
    st.session_state.student_cutoff = 0.0
    st.session_state.student_community = "OC"
    st.session_state.student_department = "All Departments"
    st.session_state.student_district = "All Districts"

    st.rerun()

# =========================================================
# PREDICT
# =========================================================

if predict:

    if not name.strip():

        st.warning(
            "⚠️ Please enter your name."
        )

    else:

        result = df.copy()

        st.session_state.student_name = name
        st.session_state.student_cutoff = cutoff
        st.session_state.student_community = community
        st.session_state.student_department = department
        st.session_state.student_district = district

        # -------------------------------------------------
        # DISTRICT
        # -------------------------------------------------

        if district != "All Districts":

            result = result[
                result["District"]
                .astype(str)
                .str.strip()
                .str.lower()
                ==
                district.strip().lower()
            ].copy()

        # -------------------------------------------------
        # DEPARTMENT
        # -------------------------------------------------

        if department != "All Departments":

            result = result[
                result["Branch"]
                .astype(str)
                .str.strip()
                .str.lower()
                ==
                department.strip().lower()
            ].copy()

        # -------------------------------------------------
        # COMMUNITY
        # -------------------------------------------------

        if community not in result.columns:

            st.error(
                f"❌ {community} cutoff column "
                "not found in dataset."
            )

            result = pd.DataFrame()

        else:

            result[community] = pd.to_numeric(
                result[community],
                errors="coerce"
            )

            result = result.dropna(
                subset=[community]
            )

        # -------------------------------------------------
        # AI CALCULATION
        # -------------------------------------------------

        if not result.empty:

            result["Difference"] = (
                cutoff -
                result[community]
            )

            result["Distance"] = abs(
                cutoff -
                result[community]
            )

            result["Match Score"] = result.apply(

                lambda row:

                calculate_match_score(
                    cutoff,
                    row[community],
                    department,
                    row["Branch"],
                    district,
                    row["District"]
                ),

                axis=1
            )

            # -------------------------------------------------
            # CHANCE
            # -------------------------------------------------

            def chance_from_score(score):

                if score >= 90:
                    return "🟢 Safe"

                elif score >= 80:
                    return "🟢 High Chance"

                elif score >= 65:
                    return "🟡 Moderate"

                elif score >= 50:
                    return "🟠 Borderline"

                else:
                    return "🔴 Low Chance"

            result["Chance"] = (
                result["Match Score"]
                .apply(chance_from_score)
            )

            # -------------------------------------------------
            # RANK
            # -------------------------------------------------

            result = (
                result
                .sort_values(
                    by=[
                        "Match Score",
                        "Distance"
                    ],
                    ascending=[
                        False,
                        True
                    ]
                )
                .reset_index(drop=True)
            )

            result["AI Rank"] = (
                result.index + 1
            )

        st.session_state.prediction_result = result

        st.rerun()

# =========================================================
# DISPLAY RESULTS
# =========================================================

if st.session_state.prediction_result is not None:

    result = (
        st.session_state.prediction_result
        .copy()
    )

    name = st.session_state.student_name
    cutoff = st.session_state.student_cutoff
    community = st.session_state.student_community
    department = st.session_state.student_department
    district = st.session_state.student_district

    # =====================================================
    # NO RESULTS
    # =====================================================

    if result.empty:

        st.error(
            "❌ No suitable colleges found."
        )

        st.info(
            "💡 Try selecting "
            "**All Districts** or "
            "**All Departments**."
        )

    else:

        # =================================================
        # SUCCESS
        # =================================================

        st.success(
            f"Hi {name}! 🎉 "
            f"AI analysed {len(result)} college options."
        )

        # =================================================
        # OVERVIEW
        # =================================================

        st.markdown(
            '<div class="section-title">'
            '🤖 AI Recommendation Overview'
            '</div>',
            unsafe_allow_html=True
        )

        best = result.iloc[0]

        average_score = round(
            result["Match Score"]
            .head(10)
            .mean(),
            1
        )

        good_count = (
            result["Chance"]
            .isin(
                [
                    "🟢 Safe",
                    "🟢 High Chance"
                ]
            )
            .sum()
        )

        o1, o2, o3, o4 = st.columns(4)

        with o1:

            st.metric(
                "🏆 Best Match",
                f"{best['Match Score']:.1f}%"
            )

        with o2:

            st.metric(
                "📊 Top 10 Average",
                f"{average_score:.1f}%"
            )

        with o3:

            st.metric(
                "🟢 Good Options",
                int(good_count)
            )

        with o4:

            st.metric(
                "🏫 Results",
                len(result)
            )

        # =================================================
        # BEST COLLEGE
        # =================================================

        st.markdown(
            '<div class="section-title">🏆 AI Best Recommendation</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="best-card">
                <span class="best-badge">🏆 TOP AI RECOMMENDATION</span>
                <div class="best-college">🏫 {best["College Name"]}</div>
                <div class="best-info">🎓 <b>Department:</b> {best["Branch"]}</div>
                <div class="best-info">📍 <b>District:</b> {best["District"]}</div>
                <div class="best-info">📊 <b>2025 {community} Cutoff:</b> {best[community]:.1f}</div>
                <div class="best-info">👤 <b>Your Cutoff:</b> {cutoff:.1f}</div>
                <div class="best-info">🎯 <b>Prediction:</b> {best["Chance"]}</div>
                <div class="best-score-container">
                    <div class="best-score">{best["Match Score"]:.1f}%</div>
                    <div class="best-score-label">AI MATCH SCORE</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.progress(float(best["Match Score"]) / 100)

        # =================================================
        # TOP 5 RECOMMENDATION CARDS
        # =================================================

        st.markdown(
            '<div class="section-title">🎯 Top College Recommendations</div>',
            unsafe_allow_html=True
        )

        top5 = result.head(5)

        for start_index in range(0, len(top5), 2):
            card_row = top5.iloc[start_index:start_index + 2]
            columns = st.columns(2)

            for column, (_, row) in zip(columns, card_row.iterrows()):
                chance = str(row["Chance"])
                if "Safe" in chance:
                    status_class = "status-safe"
                elif "High Chance" in chance:
                    status_class = "status-high"
                elif "Moderate" in chance:
                    status_class = "status-moderate"
                elif "Borderline" in chance:
                    status_class = "status-borderline"
                else:
                    status_class = "status-low"

                clean_chance = (chance.replace("🟢 ", "").replace("🟡 ", "")
                                .replace("🟠 ", "").replace("🔴 ", ""))

                with column:
                    st.markdown(
                        f"""
                        <div class="college-card">
                            <div class="college-rank">#{int(row["AI Rank"])} &nbsp;•&nbsp; AI RECOMMENDATION</div>
                            <div class="college-name">🏫 {row["College Name"]}</div>
                            <div class="college-info">🎓 <b>Department:</b> {row["Branch"]}</div>
                            <div class="college-info">📍 <b>District:</b> {row["District"]}</div>
                            <div class="college-info">📊 <b>2025 {community} Cutoff:</b> {row[community]:.1f}</div>
                            <div class="college-info">👤 <b>Your Cutoff:</b> {cutoff:.1f}</div>
                            <div style="margin-top:12px;"><span class="{status_class}">{clean_chance}</span></div>
                            <div class="score-box">
                                <div class="score-number">{row["Match Score"]:.1f}%</div>
                                <div class="score-label">AI MATCH SCORE</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

# =================================================
        # FILTER
        # =================================================

        st.markdown(
            '<div class="section-title">'
            '🔎 Search & Filter'
            '</div>',
            unsafe_allow_html=True
        )

        search = st.text_input(
            "Search College",
            placeholder="Type college name..."
        )

        filtered_result = result.copy()

        if search.strip():

            filtered_result = filtered_result[
                filtered_result["College Name"]
                .astype(str)
                .str.contains(
                    search.strip(),
                    case=False,
                    na=False
                )
            ].copy()

        f1, f2 = st.columns(2)

        with f1:

            chance_filter = st.selectbox(
                "🎯 Admission Chance",
                [
                    "All",
                    "🟢 Safe",
                    "🟢 High Chance",
                    "🟡 Moderate",
                    "🟠 Borderline",
                    "🔴 Low Chance"
                ]
            )

        with f2:

            sort_option = st.selectbox(
                "🔽 Sort Results",
                [
                    "🤖 AI Score",
                    "🎯 Best Match",
                    "📈 Highest Cutoff",
                    "📉 Lowest Cutoff",
                    "🔤 College A-Z"
                ]
            )

        if chance_filter != "All":

            filtered_result = filtered_result[
                filtered_result["Chance"]
                ==
                chance_filter
            ]

        # =================================================
        # SORT
        # =================================================

        if sort_option == "🤖 AI Score":

            filtered_result = (
                filtered_result
                .sort_values(
                    "Match Score",
                    ascending=False
                )
            )

        elif sort_option == "🎯 Best Match":

            filtered_result = (
                filtered_result
                .sort_values(
                    "Distance",
                    ascending=True
                )
            )

        elif sort_option == "📈 Highest Cutoff":

            filtered_result = (
                filtered_result
                .sort_values(
                    community,
                    ascending=False
                )
            )

        elif sort_option == "📉 Lowest Cutoff":

            filtered_result = (
                filtered_result
                .sort_values(
                    community,
                    ascending=True
                )
            )

        elif sort_option == "🔤 College A-Z":

            filtered_result = (
                filtered_result
                .sort_values(
                    "College Name"
                )
            )

        st.caption(
            f"🔎 {len(filtered_result)} "
            "colleges after filtering"
        )

        # =================================================
        # CHANCE SUMMARY
        # =================================================

        st.markdown(
            '<div class="section-title">'
            '📊 Admission Chance Overview'
            '</div>',
            unsafe_allow_html=True
        )

        counts = (
            filtered_result[
                "Chance"
            ]
            .value_counts()
        )

        q1, q2, q3, q4, q5 = st.columns(5)

        with q1:

            st.metric(
                "🟢 Safe",
                int(
                    counts.get(
                        "🟢 Safe",
                        0
                    )
                )
            )

        with q2:

            st.metric(
                "🟢 High",
                int(
                    counts.get(
                        "🟢 High Chance",
                        0
                    )
                )
            )

        with q3:

            st.metric(
                "🟡 Moderate",
                int(
                    counts.get(
                        "🟡 Moderate",
                        0
                    )
                )
            )

        with q4:

            st.metric(
                "🟠 Borderline",
                int(
                    counts.get(
                        "🟠 Borderline",
                        0
                    )
                )
            )

        with q5:

            st.metric(
                "🔴 Low",
                int(
                    counts.get(
                        "🔴 Low Chance",
                        0
                    )
                )
            )

        # =================================================
        # TOP 10 TABLE
        # =================================================

        st.markdown(
            '<div class="section-title">'
            '🏆 AI Top 10 Ranking'
            '</div>',
            unsafe_allow_html=True
        )

        top10 = (
            filtered_result
            .head(10)
            .copy()
        )

        if not top10.empty:

            ranking = pd.DataFrame({

                "Rank":
                    range(
                        1,
                        len(top10) + 1
                    ),

                "🏫 College":
                    top10[
                        "College Name"
                    ].values,

                "🎓 Department":
                    top10[
                        "Branch"
                    ].values,

                "📍 District":
                    top10[
                        "District"
                    ].values,

                "📊 Cutoff":
                    top10[
                        community
                    ].round(1).values,

                "🤖 AI Score":
                    top10[
                        "Match Score"
                    ].round(1).values,

                "🎯 Chance":
                    top10[
                        "Chance"
                    ].values
            })

            st.dataframe(
                ranking,
                use_container_width=True,
                hide_index=True
            )

        # =================================================
        # AI SCORE CHART
        # =================================================

        st.markdown(
            '<div class="section-title">'
            '📈 AI Score Comparison'
            '</div>',
            unsafe_allow_html=True
        )

        chart = (
            filtered_result[
                [
                    "College Name",
                    "Match Score"
                ]
            ]
            .head(10)
            .copy()
        )

        if not chart.empty:

            chart = chart.set_index(
                "College Name"
            )

            st.bar_chart(chart)

        # =================================================
        # DISTRICT SUMMARY
        # =================================================

        st.markdown(
            '<div class="section-title">'
            '📍 District-wise Summary'
            '</div>',
            unsafe_allow_html=True
        )

        if not filtered_result.empty:

            district_summary = (
                filtered_result
                .groupby("District")
                .agg(
                    Colleges=(
                        "College Name",
                        "nunique"
                    ),
                    Best_Score=(
                        "Match Score",
                        "max"
                    ),
                    Best_Cutoff=(
                        community,
                        "min"
                    )
                )
                .reset_index()
            )

            district_summary = (
                district_summary
                .sort_values(
                    "Best_Score",
                    ascending=False
                )
            )

            st.dataframe(
                district_summary.rename(
                    columns={
                        "District":
                            "📍 District",
                        "Colleges":
                            "🎓 Colleges",
                        "Best_Score":
                            "🤖 Best AI Score",
                        "Best_Cutoff":
                            "📉 Best Cutoff"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

        # =================================================
        # COMPARE COLLEGES
        # =================================================

        st.markdown(
            '<div class="section-title">'
            '🏫 Compare Colleges'
            '</div>',
            unsafe_allow_html=True
        )

        if not filtered_result.empty:

            college_options = (
                filtered_result[
                    "College Name"
                ]
                .drop_duplicates()
                .tolist()
            )

            selected_colleges = st.multiselect(
                "Select up to 3 colleges",
                college_options,
                max_selections=3
            )

            if selected_colleges:

                comparison = (
                    filtered_result[
                        filtered_result[
                            "College Name"
                        ].isin(
                            selected_colleges
                        )
                    ]
                    .drop_duplicates(
                        "College Name"
                    )
                )

                comparison_table = comparison[
                    [
                        "College Name",
                        "Branch",
                        "District",
                        community,
                        "Match Score",
                        "Chance"
                    ]
                ].copy()

                comparison_table = (
                    comparison_table.rename(
                        columns={
                            "College Name":
                                "🏫 College",
                            "Branch":
                                "🎓 Department",
                            "District":
                                "📍 District",
                            community:
                                "📊 2025 Cutoff",
                            "Match Score":
                                "🤖 AI Score",
                            "Chance":
                                "🎯 Chance"
                        }
                    )
                )

                st.dataframe(
                    comparison_table,
                    use_container_width=True,
                    hide_index=True
                )

        # =================================================
        # EXPORT
        # =================================================

        st.markdown(
            '<div class="section-title">'
            '📥 Export Results'
            '</div>',
            unsafe_allow_html=True
        )

        if not filtered_result.empty:

            download_data = filtered_result[
                [
                    "AI Rank",
                    "College Name",
                    "Branch",
                    "District",
                    community,
                    "Match Score",
                    "Chance"
                ]
            ].copy()

            download_data = (
                download_data.rename(
                    columns={
                        "AI Rank":
                            "AI Rank",
                        "College Name":
                            "College Name",
                        "Branch":
                            "Department",
                        "District":
                            "District",
                        community:
                            f"2025 {community} Cutoff",
                        "Match Score":
                            "AI Match Score",
                        "Chance":
                            "Admission Chance"
                    }
                )
            )

            csv_data = (
                download_data
                .to_csv(index=False)
                .encode("utf-8")
            )

            st.download_button(
                "📥 Download CSV Results",
                data=csv_data,
                file_name=(
                    "AI_college_recommendations.csv"
                ),
                mime="text/csv",
                use_container_width=True
            )

        # =================================================
        # PDF
        # =================================================

        st.markdown(
            '<div class="section-title">'
            '📄 Prediction Report'
            '</div>',
            unsafe_allow_html=True
        )

        if not filtered_result.empty:

            pdf_data = create_pdf_report(
                student_name=name,
                cutoff=cutoff,
                community=community,
                department=department,
                district=district,
                result=filtered_result
            )

            safe_name = (
                str(name)
                .strip()
                .replace(" ", "_")
            )

            st.download_button(
                "📄 Generate & Download PDF Report",
                data=pdf_data,
                file_name=(
                    f"{safe_name}_"
                    "college_prediction_report.pdf"
                ),
                mime="application/pdf",
                use_container_width=True
            )

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header(
        "🤖 AI College Predictor"
    )

    st.write(
        "Engineering College "
        "Recommendation System"
    )

    st.divider()

    st.subheader(
        "📊 Dataset"
    )

    st.write(
        "📅 Year: **2025**"
    )

    st.write(
        f"🎓 Colleges: "
        f"**{df['College Name'].nunique()}**"
    )

    st.write(
        f"📚 Departments: "
        f"**{len(departments)}**"
    )

    st.write(
        f"📍 Districts: "
        f"**{df['District'].nunique()}**"
    )

    st.divider()

    st.subheader(
        "🤖 AI Scoring"
    )

    st.write(
        "📊 Cutoff Compatibility — **70%**"
    )

    st.write(
        "🎓 Department Match — **20%**"
    )

    st.write(
        "📍 District Preference — **10%**"
    )

    st.divider()

    st.subheader(
        "🎯 Prediction Levels"
    )

    st.write("🟢 Safe")
    st.write("🟢 High Chance")
    st.write("🟡 Moderate")
    st.write("🟠 Borderline")
    st.write("🔴 Low Chance")

    st.divider()

    st.subheader(
        "📄 Reports"
    )

    st.write(
        "📥 CSV Results"
    )

    st.write(
        "📄 PDF Prediction Report"
    )

    st.divider()

    st.caption(
        "⚠️ This system uses historical "
        "2025 cutoff data and an AI-based "
        "recommendation score. It is not "
        "a guarantee of admission."
    )
