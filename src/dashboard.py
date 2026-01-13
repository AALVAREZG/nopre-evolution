"""
Streamlit Dashboard for SICAL II Budget Tracking
Visualize the evolution of budget applications over time
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from database import SicalDatabase

# Page config
st.set_page_config(
    page_title="SICAL II - Seguimiento de Aplicaciones",
    page_icon="📊",
    layout="wide"
)

# Initialize database
@st.cache_resource
def get_database():
    return SicalDatabase()

db = get_database()

# Title
st.title("📊 SICAL II - Seguimiento de Aplicaciones Presupuestarias")
st.markdown("---")

# Sidebar
st.sidebar.header("Filtros")

# Get all concepts
all_data = db.get_all_data()

if not all_data:
    st.warning("⚠️ No hay datos disponibles. Por favor, añade capturas de pantalla a la carpeta 'screenshots'.")
    st.info("""
    **Instrucciones:**
    1. Coloca capturas de pantalla de SICAL II en la carpeta `screenshots/`
    2. Ejecuta el monitor: `python src/monitor.py`
    3. El sistema procesará las imágenes automáticamente
    4. Recarga esta página para ver los datos
    """)
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(all_data)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Concept selector
concepts = df['concept'].dropna().unique()
selected_concept = st.sidebar.selectbox(
    "Seleccionar Concepto",
    options=concepts,
    format_func=lambda x: f"{x}"
)

# Filter data by selected concept
concept_df = df[df['concept'] == selected_concept].sort_values('timestamp')

# Display concept info
if not concept_df.empty:
    latest = concept_df.iloc[-1]

    st.header(f"Concepto: {selected_concept}")
    if pd.notna(latest['concept_description']):
        st.subheader(latest['concept_description'])

    st.markdown("---")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Saldo Pendiente Acreedor",
            f"€{latest['saldo_pendiente_acreedor']:,.2f}" if pd.notna(latest['saldo_pendiente_acreedor']) else "N/A"
        )

    with col2:
        st.metric(
            "Saldo Pendiente Deudor",
            f"€{latest['saldo_pendiente_deudor']:,.2f}" if pd.notna(latest['saldo_pendiente_deudor']) else "N/A"
        )

    with col3:
        st.metric(
            "Total Haber",
            f"€{latest['total_haber']:,.2f}" if pd.notna(latest['total_haber']) else "N/A"
        )

    with col4:
        st.metric(
            "Total Debe",
            f"€{latest['total_debe']:,.2f}" if pd.notna(latest['total_debe']) else "N/A"
        )

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Evolución Temporal",
        "📊 Comparativa",
        "📋 Datos Detallados",
        "🖼️ Capturas Procesadas"
    ])

    with tab1:
        st.subheader("Evolución de Saldos Pendientes")

        # Line chart for pending balances
        fig1 = go.Figure()

        if concept_df['saldo_pendiente_acreedor'].notna().any():
            fig1.add_trace(go.Scatter(
                x=concept_df['timestamp'],
                y=concept_df['saldo_pendiente_acreedor'],
                mode='lines+markers',
                name='Saldo Pendiente Acreedor',
                line=dict(color='#2ecc71', width=3)
            ))

        if concept_df['saldo_pendiente_deudor'].notna().any():
            fig1.add_trace(go.Scatter(
                x=concept_df['timestamp'],
                y=concept_df['saldo_pendiente_deudor'],
                mode='lines+markers',
                name='Saldo Pendiente Deudor',
                line=dict(color='#e74c3c', width=3)
            ))

        fig1.update_layout(
            title='Evolución de Saldos Pendientes',
            xaxis_title='Fecha',
            yaxis_title='Importe (€)',
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig1, use_container_width=True)

        # Line chart for movements
        st.subheader("Evolución de Movimientos (Haber/Debe)")

        fig2 = go.Figure()

        if concept_df['total_haber'].notna().any():
            fig2.add_trace(go.Scatter(
                x=concept_df['timestamp'],
                y=concept_df['total_haber'],
                mode='lines+markers',
                name='Total Haber',
                line=dict(color='#3498db', width=3)
            ))

        if concept_df['total_debe'].notna().any():
            fig2.add_trace(go.Scatter(
                x=concept_df['timestamp'],
                y=concept_df['total_debe'],
                mode='lines+markers',
                name='Total Debe',
                line=dict(color='#9b59b6', width=3)
            ))

        fig2.update_layout(
            title='Evolución de Movimientos',
            xaxis_title='Fecha',
            yaxis_title='Importe (€)',
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig2, use_container_width=True)

        # Propuestas M/P evolution
        st.subheader("Evolución de Propuestas de M/P")

        fig3 = go.Figure()

        if concept_df['propuestas_mp'].notna().any():
            fig3.add_trace(go.Bar(
                x=concept_df['timestamp'],
                y=concept_df['propuestas_mp'],
                name='Propuestas M/P',
                marker_color='#f39c12'
            ))

        fig3.update_layout(
            title='Propuestas de Mayor/Pago',
            xaxis_title='Fecha',
            yaxis_title='Importe (€)',
            height=400
        )

        st.plotly_chart(fig3, use_container_width=True)

    with tab2:
        st.subheader("Comparativa de Valores")

        # Calculate changes
        if len(concept_df) > 1:
            first_record = concept_df.iloc[0]
            last_record = concept_df.iloc[-1]

            comparison_data = {
                'Métrica': [
                    'Saldo Pendiente Acreedor',
                    'Saldo Pendiente Deudor',
                    'Total Haber',
                    'Total Debe',
                    'Propuestas M/P'
                ],
                'Valor Inicial': [
                    first_record['saldo_pendiente_acreedor'],
                    first_record['saldo_pendiente_deudor'],
                    first_record['total_haber'],
                    first_record['total_debe'],
                    first_record['propuestas_mp']
                ],
                'Valor Actual': [
                    last_record['saldo_pendiente_acreedor'],
                    last_record['saldo_pendiente_deudor'],
                    last_record['total_haber'],
                    last_record['total_debe'],
                    last_record['propuestas_mp']
                ]
            }

            comp_df = pd.DataFrame(comparison_data)
            comp_df['Cambio'] = comp_df['Valor Actual'] - comp_df['Valor Inicial']
            comp_df['% Cambio'] = (comp_df['Cambio'] / comp_df['Valor Inicial'] * 100).round(2)

            # Format currency
            for col in ['Valor Inicial', 'Valor Actual', 'Cambio']:
                comp_df[col] = comp_df[col].apply(lambda x: f"€{x:,.2f}" if pd.notna(x) else "N/A")

            comp_df['% Cambio'] = comp_df['% Cambio'].apply(lambda x: f"{x:,.2f}%" if pd.notna(x) else "N/A")

            st.dataframe(comp_df, use_container_width=True)

            # Bar chart comparison
            fig4 = go.Figure(data=[
                go.Bar(name='Inicial', x=comparison_data['Métrica'],
                       y=[v if pd.notna(v) else 0 for v in comparison_data['Valor Inicial']]),
                go.Bar(name='Actual', x=comparison_data['Métrica'],
                       y=[v if pd.notna(v) else 0 for v in comparison_data['Valor Actual']])
            ])

            fig4.update_layout(
                title='Comparativa Inicial vs Actual',
                barmode='group',
                height=400
            )

            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Se necesitan al menos dos registros para mostrar comparativas.")

    with tab3:
        st.subheader("Tabla de Datos Completa")

        # Display full data table
        display_df = concept_df[[
            'timestamp', 'year', 'saldo_inicial_deudor', 'saldo_inicial_acreedor',
            'total_haber', 'total_debe', 'propuestas_mp',
            'saldo_pendiente_acreedor', 'saldo_pendiente_deudor'
        ]].copy()

        # Format numbers
        numeric_cols = [
            'saldo_inicial_deudor', 'saldo_inicial_acreedor',
            'total_haber', 'total_debe', 'propuestas_mp',
            'saldo_pendiente_acreedor', 'saldo_pendiente_deudor'
        ]

        for col in numeric_cols:
            display_df[col] = display_df[col].apply(lambda x: f"€{x:,.2f}" if pd.notna(x) else "N/A")

        st.dataframe(display_df, use_container_width=True)

        # Download button
        csv = concept_df.to_csv(index=False)
        st.download_button(
            label="📥 Descargar datos (CSV)",
            data=csv,
            file_name=f"sical_concept_{selected_concept}.csv",
            mime="text/csv"
        )

    with tab4:
        st.subheader("Capturas de Pantalla Procesadas")

        processed_path = Path("processed")

        if processed_path.exists():
            images = list(processed_path.glob("*.png")) + \
                    list(processed_path.glob("*.jpg")) + \
                    list(processed_path.glob("*.jpeg"))

            # Filter images that match this concept's records
            concept_images = [img for img in images if img.name in concept_df['image_file'].values]

            if concept_images:
                # Show images in a grid
                cols = st.columns(2)

                for idx, img_path in enumerate(sorted(concept_images, reverse=True)):
                    with cols[idx % 2]:
                        # Find the record for this image
                        record = concept_df[concept_df['image_file'] == img_path.name].iloc[0]

                        st.image(str(img_path), use_container_width=True)
                        st.caption(f"📅 {record['timestamp']}")
            else:
                st.info("No hay capturas procesadas para este concepto.")
        else:
            st.info("La carpeta 'processed' no existe aún.")

else:
    st.error("No se encontraron datos para el concepto seleccionado.")

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Estadísticas Generales")
st.sidebar.metric("Total de registros", len(df))
st.sidebar.metric("Conceptos únicos", len(concepts))
st.sidebar.metric("Última actualización", df['timestamp'].max().strftime('%Y-%m-%d %H:%M'))

# Instructions
with st.sidebar.expander("ℹ️ Instrucciones"):
    st.markdown("""
    **Cómo usar:**

    1. Coloca capturas de SICAL II en `screenshots/`
    2. El monitor las procesará automáticamente
    3. Los datos aparecerán aquí
    4. Selecciona un concepto para ver su evolución

    **Archivos procesados:**
    Se mueven a la carpeta `processed/`
    """)
