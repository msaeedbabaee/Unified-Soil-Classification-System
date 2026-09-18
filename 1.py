import matplotlib.pyplot as plt
import numpy as np
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
    """Classifies soil based on the Unified Soil Classification System (USCS / ASTM D2487)."""

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
                if 4 <= pi <= 7 and pi >= a_line:
                    return "CL-ML (Silty Clay)"
                elif pi > 7 and pi >= a_line:
                    return "CL (Lean Clay)"
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
            if 4 <= pi <= 7 and pi >= a_line_val:
                return "C-M"
            elif pi > 7 and pi >= a_line_val:
                return "C"  # Clayey
            else:
                return "M"  # Silty

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


def plot_plasticity_chart(ll_input: float, pi_input: float):
    """Generates and displays the USCS Plasticity Chart with the input point."""
    fig, ax = plt.subplots(figsize=(8, 5))

    ll_vals = np.linspace(0, 100, 500)
    a_line_vals = 0.73 * (ll_vals - 20)
    u_line_vals = 0.9 * (ll_vals - 8)

    # Plot lines
    ax.plot(
        ll_vals,
        a_line_vals,
        "b-",
        label="A-Line: PI = 0.73*(LL - 20)",
        linewidth=1.5,
    )
    ax.plot(
        ll_vals,
        u_line_vals,
        "r--",
        label="U-Line: PI = 0.9*(LL - 8)",
        linewidth=1,
    )

    # Boundary lines
    ax.axvline(x=50, color="gray", linestyle=":", label="LL = 50 Line")
    ax.axhline(y=4, color="orange", linestyle="--", alpha=0.6)
    ax.axhline(y=7, color="orange", linestyle="--", alpha=0.6)

    # Shaded CL-ML region
    ax.fill_between(
        [7, 25.5], [4, 4], [7, 7], color="yellow", alpha=0.3, label="CL-ML Zone"
    )

    # User point plot
    if ll_input is not None and pi_input is not None:
        ax.plot(
            ll_input,
            pi_input,
            "ro",
            markersize=8,
            label=f"Input Soil (LL={ll_input}, PI={pi_input})",
        )

    # Formatting
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.set_xlabel("Liquid Limit (LL)", fontsize=10)
    ax.set_ylabel("Plasticity Index (PI)", fontsize=10)
    ax.set_title(
        "USCS Plasticity Chart (ASTM D2487)", fontsize=12, fontweight="bold"
    )
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper left", fontsize=8)

    st.pyplot(fig)


# --- Streamlit User Interface ---
st.set_page_config(
    page_title="Auto-Soil Classifier", page_icon="🪵", layout="centered"
)

st.title("🌱 USCS Auto-Soil Classifier")
st.write(
    "Automated soil classification tool based on **ASTM D2487 (USCS)** standard."
)

# 1. Grain Size Distribution
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

    calc_mode = st.radio(
        "Graduation Coefficients Input Method:",
        (
            "Auto-calculate from D10, D30, D60",
            "Enter Cu and Cc directly",
        ),
    )

    if calc_mode == "Auto-calculate from D10, D30, D60":
        col1, col2, col3 = st.columns(3)
        with col1:
            d10 = st.number_input("D10 (mm)", min_value=0.0001, value=0.1)
        with col2:
            d30 = st.number_input("D30 (mm)", min_value=0.0001, value=0.5)
        with col3:
            d60 = st.number_input("D60 (mm)", min_value=0.0001, value=1.2)

        cu = d60 / d10 if d10 > 0 else 0.0
        cc = (d30**2) / (d10 * d60) if (d10 * d60) > 0 else 0.0

        st.info(f"**Calculated Coefficients:** $C_u = {cu:.2f}$ | $C_c = {cc:.2f}$")
    else:
        cu = st.number_input(
            "Coefficient of Uniformity (Cu)", min_value=0.0, value=5.0
        )
        cc = st.number_input(
            "Coefficient of Curvature (Cc)", min_value=0.0, value=2.0
        )
else:
    retained_4_of_coarse = 0.0
    cu = None
    cc = None

# 2. Atterberg Limits
st.subheader("2. Atterberg Limits")
has_atterberg = st.checkbox("Include Atterberg Limits data", value=True)

if has_atterberg:
    col_ll, col_pi = st.columns(2)
    with col_ll:
        ll = st.number_input("Liquid Limit (LL)", min_value=0.0, value=35.0)
    with col_pi:
        pi = st.number_input("Plasticity Index (PI)", min_value=0.0, value=12.0)
else:
    ll = None
    pi = None

# 3. Organic Properties
st.subheader("3. Organic Soil Test")
is_organic_test = st.checkbox("Organic soil test / High organic content")
if is_organic_test:
    col_org1, col_org2 = st.columns(2)
    with col_org1:
        organic_content = st.number_input(
            "Organic Content (%)", min_value=0.0, max_value=100.0, value=0.0
        )
    with col_org2:
        ll_oven_dried = st.number_input(
            "Oven-Dried Liquid Limit (LL)",
            min_value=0.0,
            value=0.0,
        )
else:
    organic_content = 0.0
    ll_oven_dried = None

# Classification Execution
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

    st.success(f"### **USCS Classification Result:** `{result}`")

    # Display Plasticity Chart if LL and PI are provided
    if ll is not None and pi is not None:
        st.subheader("📊 Plasticity Chart")
        plot_plasticity_chart(ll_input=ll, pi_input=pi)
