# -*- coding: utf-8 -*-
"""
Created on Wed Jun 25 20:14:22 2025

@author: osgos
"""

from app_persistencia import Persistencia
import pandas as pd
import streamlit as st
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import kaleido
import os

class app_dashboard_mantto:
#Función de persistencia para la aplicación.
    def __init__(self):
        self.persistencia = Persistencia()
        self.df_main = self.persistencia.df_extended
        self.df_tech = self.persistencia.df_mp
        
#Función para clasificar a los técnicos según su MTTR
    def _clasificar_mttr(self, valor):
        if pd.isna(valor):
            return "Sin datos"
        elif valor > 10:
            return "Oportunidad"
        elif valor > 1.2:
            return "Regular"
        elif valor > 0.7:
            return "Bueno"
        else:
            return "Sobresaliente"
    
#Función para clasificar a los técnicos de acuerdo a su Strategic Ratio    
    def _clasificar_sr(self, valor):
        if pd.isna(valor):
            return "Altamente reactivo"
        elif valor >= 1:
            return "Correctivo"
        elif valor >= 0.7:
            return "Regular"
        elif valor >= 0.4:
            return "Preventivo"
        else:
            return "Proactivo"

#Visualizar análisis por técnicos.    
    def view_tech_data(self):
        st.set_page_config(page_title='Reportes Rápidos: Técnicos', page_icon="📑")
        st.subheader("Métricas de desempeño por  técnico de mantenimiento")
        col1, col2 = st.columns(2)
        with col1:
            tech_list = self.df_tech['nombre'].unique()
            select_tech = st.selectbox('Selecciona un técnico', tech_list, index=0)
        with col2:
            self.df_main['Mes'] = self.df_main['Fecha Creacion OT'].dt.month_name(locale='es_ES')
            months = self.df_main['Mes'].dropna().unique()
            mes_orden = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                         'Julio', 'Agosto', 'Septiembre', 'Octubure', 'Noviembre', 'Diciembre']
            all_month = ["Todos"] + sorted(months, key=lambda x:  mes_orden.index(x))
            selec_month = st.selectbox('Selecciona un mes', all_month, key="tabla_mes")

        #Mostrar estadísticos de técnico de mantenimiento seleccionado
        #Calcula el total de órdenes atendidas, horas registradas en sistema,
        #Tiempo medio de reparación y promedio de tiempo de paro.
        id_tech = self.df_tech[self.df_tech['nombre'] == select_tech]['num_tecnico'].values
        if len(id_tech) == 0:
            st.error("No se encontró el ID de este técnico.")
            return
        else:
            id_tech = id_tech[0]
        if selec_month == "Todos":
            df_filter = self.df_main[(self.df_main['E_Number'] == id_tech) &
                                     (self.df_main["OT Estado"].isin(["CLOSE", "COMP"]))]
        else:
            df_filter = self.df_main[
                (self.df_main['E_Number'] == id_tech) &
                (self.df_main['Mes'] == selec_month) &
                (self.df_main["OT Estado"].isin(["CLOSE", "COMP"]))]
        #Muestra el resumen de métricas de desempeño del técnico seleccionado.
        total_orders = df_filter['Orden de trabajo'].count()
        total_hours = df_filter['Duración'].sum()
        MTTR = df_filter['Duración_OT'].mean()
        downtime_avg = df_filter["Tiempo Parada"].mean()
        #Acceder al registro de la orden con mayor duración
        df_grouped = df_filter.groupby('Orden de trabajo', as_index=False).agg({
            'Duración_OT': 'sum', 'OT Descripción': 'first',
            'Ubicación': 'first',
            'Tipo de trabajo': 'first',
            'Síntoma': 'first',
            'Fecha Creacion OT': 'first',
            'Depende de': 'first',
            'Tiempo Parada': 'sum',
            'Coste Actual PDR': 'sum',
            'Descripcion Larga OT': 'first',
            })
        df_top10 = df_grouped.sort_values('Duración_OT', ascending=False).head(10)
        top5_list = df_top10['Orden de trabajo'].astype(str).tolist()
        st.write('**Métricas de desemepeño del técnico seleccionado**')
        col1, col2 = st.columns(2)
        with col1:
            st.write('**Órdenes atendidas**', int(total_orders))
            st.write('**Horas registradas**', f"{total_hours:.1f} h")
        with col2:
            #Añadir una etiqueta a los técnicos basados en sus datos de MTTR
            categoria = self._clasificar_mttr(MTTR)
            colores = {
                "Oportunidad": "🔴",
                "Regular": "🟠",
                "Bueno": "🟡",
                "Sobresaliente": "🟢",
                "Sin datos": "⚪"}
            emoji = colores.get(categoria, "⚪")
            st.write("**MTTR**", f"{MTTR:.2f} h ({emoji} {categoria})")
            st.write("**Promedio tiempo muerto**", f"{downtime_avg:.2f} h")
        
        #Mostrar una clasificación al técnico de acuerdo al tipo de órdenes que atiende.
        tipo_orden = df_filter['Tipo de trabajo'].value_counts()
        D  = tipo_orden.get("Correctivo", 0)
        E  = tipo_orden.get("Preventivo", 0)
        E1 = tipo_orden.get("Predictivo", 0)
        S  = tipo_orden.get("Seguridad", 0)
        I  = tipo_orden.get("Inspección", 0)
        #Variable para analizar el denominador y evitar errores al divivir entre cero
        denominador = E + E1 + S + I + D
        #Çálculo de Strategic Ratio del Técnico
        if denominador != 0:
            SR = D / denominador
        else:
            SR = float("nan")
        
        emoji_sr = {
            "Correctivo": "🔴",
            "Regular": "🟠",
            "Preventivo": "🟡",
            "Proactivo": "🟢",
            "Altamente reactivo": "⚪"}
        
        categoria_sr = self._clasificar_sr(SR)
        icono = emoji_sr.get(categoria_sr, "⚪")
        st.write("**Índice SR (Correctivo/Total):**", f"{SR:.2f} ({icono} {categoria_sr})")
        
        col1, col2 = st.columns(2)
        with col1:
            ot_select = st.selectbox('Top 10: Selecciona una orden para ver los detalles', top5_list)
        with col2:
            #Exportar reporte del Top 10 de fallas del técnico seleccionado.
            if st.button("💾 Exportar top 10 órdenes"):
                try:
                    os.makedirs('resultados', exist_ok=True)
                    path_csv = os.path.join('resultados', 'top10_ordenes.csv')
                    df_top10.to_csv(path_csv, index=False)
                    st.success(f"✅Top 10 exportado a: {path_csv}")
                except Exception as e:
                    st.error(f"❌Error al exportar: {e}")
            
        OT = df_top10[df_top10['Orden de trabajo'].astype(str) == ot_select].iloc[0]
        with st.expander(f"Mostrar detalles de órdenes **{select_tech}**"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Número de Orden:** {OT['Orden de trabajo']}")
                st.write(f"**Duración:** {OT['Duración_OT']: .2f} h")
                st.write(f"**Naturaleza:** {OT['Depende de']}")
                st.write(f"**Tipo de Orden:** {OT['Tipo de trabajo']}")
            with col2:
                st.write(f"**Descripción:** {OT['OT Descripción']}")
                st.write(f"**Tiempo de paro:** {OT['Tiempo Parada']: .2f} h")
                st.write(f"**Costo de reparación:** {OT['Coste Actual PDR']: .2f} USD")
                prosore = OT["Descripcion Larga OT"]
                cond_prosore = (
                                    "No se registró información"
                                    if pd.isna(prosore) or prosore == ""
                                    else prosore
                                    )
                st.write(f"**PROSORE:** {cond_prosore}")
        
        
        df_tipo = df_filter.groupby(["Tipo de trabajo", "Depende de"], observed=True).size().reset_index(name='Órdenes')
        
        #Gráfica de distribución número de órdenes atendidas:

        fig_tipo = px.bar(
            df_tipo,
            x="Tipo de trabajo",
            y="Órdenes",
            color='Depende de',
            text_auto=True,
            color_continuous_scale="Blues",
            labels={"Tipo de trabajo": "Tipo de trabajo", "Órdenes": "Número de órdenes"},
            title=f"Órdenes por tipo de trabajo y naturaleza - {selec_month.capitalize()}",
        )
        
        fig_tipo.update_layout(
            xaxis_title=None,
            yaxis_title="Órdenes",
            height=400,
            coloraxis_showscale=False
        )
        
        st.plotly_chart(fig_tipo, use_container_width=True)

#Visualización de análisis por máquina        
    def view_machine_data(self):
        st.set_page_config(page_title='Reportes Rápidos: Máquina', page_icon="🔩")
        #Análisis de activos con peor desempeño.
        st.subheader("Esta gráfica muestra los Top 10 de máquinas con más fallas y el tipo de fallas")
        self.df_main["Mes"] = self.df_main["Fecha Creacion OT"].dt.month_name(locale="es_ES").str.capitalize()
        df_Filter_D = self.df_main[self.df_main['Tipo de trabajo'] == 'D'] #Filtra únicamente las órdenes correctivas: Tipo D
        
        #Crear filtro por grupo de trabajo y meses.
        col1, col2 = st.columns(2)
        with col1:
            #Añade un filtro por meses para las gráficas.
            months = self.df_main['Mes'].dropna().unique()
            mes_orden = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                         'Julio', 'Agosto', 'Septiembre', 'Octubure', 'Noviembre', 'Diciembre']
            all_month = ["Todos"] + sorted(months, key=lambda x:  mes_orden.index(x))
            selec_month = st.selectbox('Selecciona un mes', all_month, key="tabla_mes")
            if selec_month != 'Todos':
                df_Filter_D = df_Filter_D[df_Filter_D['Mes'] == selec_month]
        with col2:
            #Crear un filtro por grupos de trabajo.
            shift_raw = self.df_main['Turnos'].dropna().str.split(",")
            turnos = [t.strip() for sublist in shift_raw for t in sublist if t.strip() != ""]
            turnos_filter = sorted(set(turnos))
            selec_turno = st.multiselect('Selecciona turnos', turnos_filter, default=turnos_filter)
            todos_turnos = set(selec_turno) == set(turnos_filter)
            turnos_visibles = "Todos" if todos_turnos else ", ".join(selec_turno)
            df_Filter_D = df_Filter_D[df_Filter_D['Turnos'].fillna("").apply(lambda cadena: any(t in cadena.split(",") for t in selec_turno))]

#####GRÁFICAS DE ANÁLISIS DE FALLAS Y MAPA DE CALOR.            
        
        col1, col2 = st.columns(2) #Agregar gráficos en columnas.
        with col1:
            df_top_maq = df_Filter_D['Ubicación'].value_counts().reset_index(name='num_fallas') #Cuenta el número de fallas por cada máquina.
            df_top_maq.columns = ['Máquina', 'num_fallas']
            df_top10 = df_top_maq.head(10)
            
            df_downtime = df_Filter_D.groupby("Ubicación", as_index=False)['Tiempo Parada'].sum()
            df_downtime.columns = ['Máquina', 'Tiempo Parada']
            
            df_pareto = pd.merge(df_top10, df_downtime, on='Máquina', how='left')
            
            fig_pareto = make_subplots(specs=[[{'secondary_y': True}]])
            fig_pareto.add_trace(
                go.Bar(
                    x=df_pareto['Máquina'],
                    y=df_pareto["num_fallas"],
                    name="Número de fallas",
                    marker_color="indianred",
                    text=df_pareto["num_fallas"],
                    textposition="auto"
                    ),
                secondary_y=False)
            
            fig_pareto.add_trace(
                go.Scatter(
                    x=df_pareto["Máquina"],
                    y=df_pareto["Tiempo Parada"],
                    name="Tiempo total de parada",
                    mode="lines+markers",
                    line=dict(color="darkblue", width=3),
                    marker=dict(size=8),
                    yaxis="y2"
                    ),
                secondary_y=True)
            
            fig_pareto.update_layout(
                title="Top 10 máquinas: Fallas vs Tiempo total de parada",
                xaxis_title="Máquina",
                yaxis_title="Número de fallas",
                height=460,
                legend=dict(x=0.01, y=1.12, orientation="h"),
                margin=dict(t=60, b=50),
            )

            fig_pareto.update_yaxes(title_text="Número de fallas", secondary_y=False)
            fig_pareto.update_yaxes(title_text="Tiempo de paro (min)", secondary_y=True)

            st.plotly_chart(fig_pareto, use_container_width=True)
            
        with col2:
            #Crear un dataframe para analizar los tipos de falla dados por la columna 'Síntoma'
            #Resumen de fallas:
            fail_class = {
                "GENERAL SEGURIDAD": "SEGURIDAD",
                "GENERAL SISTEMAS DE INFORMACION": "SISTEMAS",
                "GENERAL HIDRAULICO Y NEUMATICO": "HIDRÁULICO Y NEUMATICO",
                "GENERAL MECHANICAL": "MECÁNICO",
                "GENERAL ELECTRICO Y AUTOMATIZACION": "ELECTRICO"}
            df_Filter_D['Fail_resume'] = df_Filter_D['Síntoma'].map(fail_class).fillna("OTROS")
            df_sintoma = df_Filter_D['Fail_resume'].value_counts().reset_index(name='Frecuencia')
            df_sintoma.columns = ['Tipo de Falla', 'Frecuencia']
            df_expanded = df_sintoma.loc[df_sintoma.index.repeat(df_sintoma['Frecuencia'])].reset_index(drop=True)
                        
            fig_falla = px.density_heatmap(
                df_expanded,
                y="Tipo de Falla",  # Lo mostramos en vertical para que quepa mejor
                nbinsy=len(df_sintoma),
                color_continuous_scale="Purples",
                title="Distribución de fallas por tipo",
                labels={"Tipo de falla": "Tipo de Falla", "count": "Frecuencia"})
            
            fig_falla.update_layout(
                height=460,
                xaxis_visible=False)
            st.plotly_chart(fig_falla, use_container_width=True)
            
        with st.expander(f"Resumen de fallas en el mes: **{selec_month}** y en los turnos: **{turnos_visibles}**"):
            st.write(df_pareto)
            
        
#GUARDAR DATOS E IMPRIMIR REPORTES.
        st.subheader("Imprimir reporte y exportar datos")
        custom_path = st.checkbox("Elegir ruta personalizada")
        
        if custom_path:
            ruta_base = st.text_input("📂 Ruta del directorio:")
            nombre_archivo = st.text_input("📝 Nombre base del archivo (sin extensión)", value="mi_reporte")
        else:
            ruta_base = "resultados"
            nombre_archivo = "my_report"
        
        if st.button("📥 Exportar CSV y gráficas"):
            try:
                os.makedirs(ruta_base, exist_ok=True) #Valida que la carpeta resultados exista.
        
                # Definir rutas en variables para hacer más legible el código.
                ruta_csv = os.path.join(ruta_base, f"{nombre_archivo}.csv")
                ruta_img1 = os.path.join(ruta_base, f"{nombre_archivo}_maquinas.png")
                ruta_img2 = os.path.join(ruta_base, f"{nombre_archivo}_fallas.png")
        
                # Guardar CSV
                df_pareto.to_csv(ruta_csv, index=False)
        
                # Guardar figuras como imagen usando el método write_image() de las figuras
                fig_pareto.write_image(ruta_img1, format="png", scale=2)
                fig_falla.write_image(ruta_img2, format="png", scale=2)
        
                st.success(f"✅ Archivos exportados con éxito en: {ruta_base}")
                st.write(f"- CSV: `{ruta_csv}`")
                st.write(f"- Imagen 1: `{ruta_img1}`")
                st.write(f"- Imagen 2: `{ruta_img2}`")
        
            except Exception as e:
                st.error(f"❌ Error al guardar los archivos: {e}")

#Selector de vistas para el usuario.        
    def run(self):
        st.sidebar.title("Menu")
        opcion = st.sidebar.radio('Ir a:', ["Técnicos", "Máquina"])
        if opcion == 'Técnicos':
            self.view_tech_data()
        elif opcion == 'Máquina':
            self.view_machine_data()

#Ejecuta la aplicación validando si se corre desde el main.
if __name__ == "__main__":
    App = app_dashboard_mantto()
    App.run()