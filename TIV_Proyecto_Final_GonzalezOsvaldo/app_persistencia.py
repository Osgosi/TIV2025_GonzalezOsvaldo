# -*- coding: utf-8 -*-
"""
Created on Wed Jun 25 20:15:14 2025

@author: osgos
"""

import numpy as np
import pandas as pd
import streamlit as st
import os

#Carga del archivo a un data set para comenzar con la manipulación de datos del registro de base de datos.


class Persistencia:
    def __init__(self):
        self.path_main = os.path.join(os.getcwd(), 'datos/Dataset.xlsx')
        self.path_mp = os.path.join(os.getcwd(), 'datos/mtto_people.csv')
        self.df_bma = None
        self.df_mp = None
        self.carga_datos()
        
    def carga_datos(self):
        try:
            self.df_bma = pd.read_excel(self.path_main, sheet_name="bma_data")
            self.df_mp = pd.read_csv(self.path_mp)
            print(f"Datos cargados correctamente.")
        except Exception as e:
            print(f"Error al leer los archivos: {e}")
        
        #Método para separa la columna 'Codigos Mano de Obra' en filas independientes
        #por técnico.
        df_bma_extend = self.df_bma.dropna(subset=['Codigos Mano de Obra']).copy()
        df_bma_extend = df_bma_extend.assign(E_Number=df_bma_extend['Codigos Mano de Obra'].str.split(",")).explode('E_Number')
        df_bma_extend['E_Number'] = df_bma_extend['E_Number'].str.strip()
        
        df_merged = df_bma_extend.merge(self.df_mp, left_on='E_Number', right_on='num_tecnico', how='left')
        #Atributo para usar en la clase de visualización
        self.df_extended = df_merged
        
        