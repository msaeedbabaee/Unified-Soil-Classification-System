import streamlit as st


def classify_soil(
    passing_200: float,
    retained_4_of_coarse: float,
    cu: float = None,
    cc: float = None,
    ll: float = None,
    pi: float = None,
    organic_content: float = 0.0,
    ll_oven_dried: float = None,
) -> str:
    """Classifies soil based on the Unified Soil Classification System (USCS / ASTM D2487).

    Parameters:
    - passing_200: Percentage passing No. 200 sieve (0.075 mm)
    - retained_4_of_coarse: Percentage of coarse fraction retained on No. 4
    sieve (4.75 mm)
    - cu: Coefficient of Uniformity (D60 / D10)
    - cc: Coefficient of Curvature ((D30)^2 / (D10 * D60))
    - ll: Liquid Limit
    - pi: Plasticity Index
    - organic_content: Organic matter percentage
    - ll_oven_dried: Liquid limit after oven drying (for organic soil test)
    """

    # 1. Highly organic soils check (Peat)
    if organic_content > 75:
        return "PT (Peat)"

    # 2. Organic soil determination (OL / OH)
    is_organic = False
    if organic_content > 5:
        is_organic = True
    if (
        ll_oven_dried is not None
        and ll is not None
        and ll > 0
        and (ll_oven_dried / ll) < 0.75
    ):
        is_organic = True

    # 3. Fine-grained soils (>= 50% passing No. 200 sieve)
    if passing_200 >= 50:
        if ll is None or pi is None:
            return "Error: Liquid Limit (LL) and Plasticity Index (PI) are required for fine-grained soils."

        a_line = 0.73 * (ll - 20)

        if ll < 50:
            if is_organic:
                return "OL (Organic Silt or Organic Clay)"
            else:
                if pi > 7 and pi >= a_line:
                    return "CL (Lean Clay)"
                elif pi < 4 or pi < a_line:
                    return "ML (Silt)"
                elif 4 <= pi <= 7 and pi >= a_line:
                    return "CL-ML (Silty Clay)"
                else:
                    return "ML (Silt)"
        else:  # LL >= 50
            if is_organic:
                return "OH (Organic Clay or Organic Silt)"
            else:
                if pi >= a_line:
                    return "CH (Fat Clay)"
                else:
                    return "MH (Elastic Silt)"

    # 4. Coarse-grained soils (< 50% passing No. 200 sieve)
    else:
        fines_percent = passing_200
        is_gravel = retained_4_of_coarse > 50

        # Helper function to determine fines classification
        def get_fines_type():
            if ll is None or pi is None:
                return "M"
            a_line_val = 0.73 * (ll - 20)
            if pi > 7 and pi >= a_line_val:
                return "C"  # Clayey
            elif pi < 4 or pi < a_line_val:
                return "M"  # Silty
            elif 4 <= pi <= 7 and pi >= a_line_val:
                return "C-M"
            return "M"

        # Graduation criteria evaluation
        if is_gravel:
            prefix = "G"
            well_graded = (
                (cu is not None and cu >= 4)
                and (cc is not None)
                and (1 <= cc <= 3)
            )
        else:
            prefix = "S"
            well_graded = (
                (cu is not None and cu >= 6)
                and (cc is not None)
                and (1 <= cc <= 3)
            )

        # Case A: Less than 5% fines (Clean coarse-grained soils)
        if fines_percent < 5:
            return f"{prefix}W" if well_graded else f"{prefix}P"

        # Case B: More than 12% fines (Coarse-grained soils with fines)
        elif fines_percent > 12:
            f_type = get_fines_type()
            return f"{prefix}{f_type}"

        # Case C: 5% to 12% fines (Dual symbols)
        else:
            grad = f"{prefix}W" if well_graded else f"{prefix}P"
            f_type = get_fines_type()
            return f"{grad}-{prefix}{f_type}"


# --- Streamlit User Interface ---
st.set_page_config(
    page_title="USCS Soil Classifier", page_icon="🪵", layout="centered"
)

st.title("🌱 USCS Soil Classification Tool")
st.write(
    "Classify soil based on Unified Soil Classification System (ASTM D2487)."
)

st.subheader("1. Grain Size Distribution")
passing_200 = st.number_input(
    "Percentage passing No. 200 sieve (%)",
    min_value=0.0,
    max_value=100.0,
    value=20.0,
)

if passing_200 < 50:
    retained_4_of_coarse = st.number_input(
        "Percentage of coarse fraction retained on No. 4 sieve (%)",
        min_value=0.0,
        max_value=100.0,
        value=60.0,
    )
    cu = st.number_input(
        "Coefficient of Uniformity (Cu)", min_value=0.0, value=5.0
    )
    cc = st.number_input("Coefficient of Curvature (Cc)", min_value=0.0, value=2.0)
else:
    retained_4_of_coarse = 0.0
    cu = None
    cc = None

st.subheader("2. Atterberg Limits")
has_atterberg = st.checkbox("Include Atterberg Limits data", value=True)

if has_atterberg:
    ll = st.number_input("Liquid Limit (LL)", min_value=0.0, value=35.0)
    pi = st.number_input("Plasticity Index (PI)", min_value=0.0, value=12.0)
else:
    ll = None
    pi = None

st.subheader("3. Organic Properties (Optional)")
is_organic_test = st.checkbox("Organic soil test / High organic content")
if is_organic_test:
    organic_content = st.number_input(
        "Organic Content (%)", min_value=0.0, max_value=100.0, value=0.0
    )
    ll_oven_dried = st.number_input(
        "Oven-dried Liquid Limit (LL)", min_value=0.0, value=0.0
    )
else:
    organic_content = 0.0
    ll_oven_dried = None

# Classification execution
if st.button("Classify Soil", type="primary"):
    result = classify_soil(
        passing_200=passing_200,
        retained_4_of_coarse=retained_4_of_coarse,
        cu=cu,
        cc=cc,
        ll=ll,
        pi=pi,
        organic_content=organic_content,
        ll_oven_dried=ll_oven_dried,
    )

    st.success(f"**Classification Result:** {result}")
