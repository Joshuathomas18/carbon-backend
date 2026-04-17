import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
import shapely.wkt
from shapely.geometry import shape
from app.config import settings

# 1. Page Configuration
st.set_page_config(
    page_title="Carbon_kheth | God View",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Styling (Clean Light Mode)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Simple Password Protection
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.sidebar.title("🔐 Secure Login")
        pwd = st.sidebar.text_input("Enter Dashboard Password", type="password")
        if st.sidebar.button("Login"):
            if pwd == "carbon2024": # Simple sprint password
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.sidebar.error("Invalid Password")
        st.info("Please log in to view the Carbon Ledger.")
        return False
    return True

# 4. Data Fetching
@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def fetch_dashboard_data(client: Client):
    # Fetch all farmers
    farmers_resp = client.table("farmers").select("*").execute()
    farmers = pd.DataFrame(farmers_resp.data)
    
    # Fetch all plots
    plots_resp = client.table("plots").select("*").execute()
    plots = pd.DataFrame(plots_resp.data)
    
    # Fetch all scores
    scores_resp = client.table("carbon_scores").select("*").execute()
    scores = pd.DataFrame(scores_resp.data)
    
    return farmers, plots, scores

# Main App Logic
if check_password():
    client = get_supabase_client()
    
    try:
        farmers, plots, scores = fetch_dashboard_data(client)
        
        # Sidebar: Farmer Selection
        st.sidebar.title("🌳 Mission Control")
        st.sidebar.markdown("---")
        
        if not farmers.empty:
            farmer_options = ["All Farmers"] + farmers['phone'].tolist()
            selected_farmer_phone = st.sidebar.selectbox("Select Farmer (Phone)", farmer_options)
            
            # Filter logic
            if selected_farmer_phone != "All Farmers":
                farmer_id = farmers[farmers['phone'] == selected_farmer_phone]['id'].iloc[0]
                filtered_plots = plots[plots['farmer_id'] == farmer_id]
                selected_farmer_name = farmers[farmers['phone'] == selected_farmer_phone]['name'].iloc[0]
            else:
                filtered_plots = plots
                selected_farmer_name = "Global View"
        else:
            st.warning("No farmers found in database.")
            filtered_plots = pd.DataFrame()
            selected_farmer_name = "No Data"

        # --- Dashboard Header ---
        st.title(f"🌍 {selected_farmer_name} | Carbon God View")
        
        # --- Top Metrics ---
        col1, col2, col3, col4 = st.columns(4)
        
        total_tonnes = scores[scores['plot_id'].isin(filtered_plots['id'])]['total_tonnes_co2'].sum() if not filtered_plots.empty else 0
        total_value = total_tonnes * 40 # Standard ₹40 rate
        avg_confidence = scores[scores['plot_id'].isin(filtered_plots['id'])]['confidence_score'].mean() if not filtered_plots.empty else 0
        
        with col1:
            st.metric("Total Carbon Tonnes", f"{total_tonnes:.2f} T")
        with col2:
            st.metric("Portfolio Value", f"₹{total_value:,.2f}")
        with col3:
            st.metric("Verification Confidence", f"{avg_confidence*100:.1f}%")
        with col4:
            st.metric("Registered Plots", len(filtered_plots))

        # --- Map & Details ---
        m_col, d_col = st.columns([2, 1])

        with m_col:
            st.subheader("Farm Boundaries & Carbon Heatmap")
            
            # Default center (India)
            map_center = [20.5937, 78.9629]
            zoom = 5
            
            if not filtered_plots.empty:
                # Get center from the first plot for zoom-to
                try:
                    first_geom = filtered_plots.iloc[0]['geometry']
                    if isinstance(first_geom, dict):
                        poly = shape(first_geom)
                    else:
                        if "SRID=4326;" in first_geom:
                            first_geom = first_geom.split(";")[-1]
                        poly = shapely.wkt.loads(first_geom)
                    
                    centroid = poly.centroid
                    map_center = [centroid.y, centroid.x]
                    zoom = 15
                except Exception as e:
                    logger.error(f"Error calculating map center: {e}")

            m = folium.Map(location=map_center, zoom_start=zoom, tiles="OpenStreetMap")
            
            # Add Polygons to Map
            for _, plot in filtered_plots.iterrows():
                try:
                    geom_data = plot['geometry']
                    
                    # 1. Handle GeoJSON Dict
                    if isinstance(geom_data, dict):
                        poly = shape(geom_data)
                    # 2. Handle WKT String
                    else:
                        if "SRID=4326;" in geom_data:
                            geom_data = geom_data.split(";")[-1]
                        poly = shapely.wkt.loads(geom_data)

                    # Folium expects [[lat, lon], ...]
                    if poly.geom_type == 'Polygon':
                        coords = [[p[1], p[0]] for p in poly.exterior.coords]
                    elif poly.geom_type == 'MultiPolygon':
                        # Just take the first polygon for demo or render all
                        coords = [[p[1], p[0]] for p in poly.geoms[0].exterior.coords]
                    else:
                        continue
                    
                    # Get score for popup
                    plot_score = scores[scores['plot_id'] == plot['id']]
                    popup_text = f"Plot ID: {plot['id']}<br>Area: {plot['area_hectares']}ha"
                    if not plot_score.empty:
                        popup_text += f"<br>Carbon: {plot_score.iloc[0]['total_tonnes_co2']:.2f} T"
                    
                    folium.Polygon(
                        locations=coords,
                        color="green",
                        fill=True,
                        fill_color="lime",
                        fill_opacity=0.4,
                        popup=popup_text
                    ).add_to(m)
                except Exception as e:
                    st.error(f"Error rendering plot {plot['id']}: {e}")

            st_folium(m, width="100%", height=500, key="main_map")

        with d_col:
            st.subheader("Satellite Breakdown")
            if not filtered_plots.empty:
                # Show breakdown for the first selected plot
                selected_plot = filtered_plots.iloc[0]
                plot_score = scores[scores['plot_id'] == selected_plot['id']]
                
                if not plot_score.empty:
                    breakdown = plot_score.iloc[0]['breakdown']
                    df_breakdown = pd.DataFrame([
                        {"Source": "Soil Carbon", "Value": breakdown.get("soc_removals", 0)},
                        {"Source": "Fertilizer Opt", "Value": breakdown.get("fert_reductions", 0)},
                        {"Source": "Fire Prevention", "Value": breakdown.get("burn_reductions", 0)},
                    ])
                    
                    fig = px.pie(df_breakdown, values='Value', names='Source', 
                                title="Contribution Mix", hole=0.4,
                                color_discrete_sequence=px.colors.sequential.Greens_r)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.info(f"""
                        **Methodology:** {plot_score.iloc[0]['methodology']}  
                        **Calculated At:** {plot_score.iloc[0]['calculated_at']}
                    """)
                else:
                    st.info("No detailed score breakdown available for this plot yet.")
                
                # Plot Metadata
                st.markdown("### Environmental Factors")
                metadata = selected_plot.get('plot_metadata', {})
                st.write(f"🌧️ **Rainfall:** {metadata.get('rainfall_mm', 'N/A')} mm")
                st.write(f"📈 **NDVI Health:** {metadata.get('ndvi_median', 'N/A')}")
            else:
                st.info("Select a farmer to see detailed drill-down.")

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        st.info("Ensure your Supabase URL and Key are correct in .env and tables are created.")
