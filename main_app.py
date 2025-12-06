import customtkinter as ctk
from tkinter import messagebox
from db_manager import DBManager
from datetime import date 

# Constante para el stock mínimo, como solicitaste
STOCK_MINIMO = 10

# Configuración de CustomTkinter
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue")

# --- CLASE MODAL ---

class AddEditCategoryModal(ctk.CTkToplevel):
    """Modal (Ventana emergente) para agregar o editar categorías."""
    def __init__(self, master, title, save_command, initial_name=""):
        super().__init__(master)
        self.title(title)
        self.geometry("300x150")
        self.resizable(False, False)
        
        self.transient(master) 
        self.grab_set() 

        self.save_command = save_command
        
        self.label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        self.label.pack(pady=10)

        self.entry_nombre = ctk.CTkEntry(self, placeholder_text="Nombre de la Categoría", width=250)
        self.entry_nombre.pack(pady=5)
        self.entry_nombre.insert(0, initial_name) 

        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=10)
        
        btn_registrar = ctk.CTkButton(self.button_frame, text="Registrar" if not initial_name else "Guardar", command=self.save_action, width=100)
        btn_registrar.grid(row=0, column=0, padx=5)
        
        btn_cancelar = ctk.CTkButton(self.button_frame, text="Cancelar", command=self.destroy, fg_color="gray", hover_color="darkgray", width=100)
        btn_cancelar.grid(row=0, column=1, padx=5)

    def save_action(self):
        nombre = self.entry_nombre.get().strip()
        if self.save_command(nombre):
            self.destroy()

# --- CLASE DE VISTA: VER PRODUCTO ---

class VerProductoPage(ctk.CTkFrame):
    """Muestra los detalles de un producto seleccionado."""
    def __init__(self, master, db_manager, producto_id, parent_page):
        super().__init__(master, corner_radius=0)
        self.db_manager = db_manager
        self.producto_id = producto_id
        self.parent_page = parent_page 
        
        self.grid_columnconfigure(0, weight=1)

        # Título y Subtítulo
        self.title_label = ctk.CTkLabel(self, text="VER PRODUCTO", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=0, pady=(0, 5), sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(self, text="Detalles del producto seleccionado", font=ctk.CTkFont(size=16))
        self.subtitle_label.grid(row=1, column=0, padx=0, pady=(0, 20), sticky="w")
        
        self.details_frame = ctk.CTkFrame(self)
        self.details_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        self.details_frame.grid_columnconfigure((0, 1), weight=1)

        self.load_product_details()
        
        # Botón Volver
        btn_back = ctk.CTkButton(self, text="← Volver al Inventario", command=self.go_back)
        btn_back.grid(row=3, column=0, padx=20, pady=20, sticky="w")
        
    def load_product_details(self):
        """Carga y muestra los detalles del producto desde la DB."""
        for widget in self.details_frame.winfo_children():
            widget.destroy()

        datos_producto = self.db_manager.obtener_producto_por_id(self.producto_id)
        
        if datos_producto:
            codigo, nombre, categoria, laboratorio = datos_producto
            
            data_map = {
                "Código:": codigo,
                "Nombre del Producto:": nombre,
                "Categoría:": categoria,
                "Laboratorio:": laboratorio,
            }
            
            for i, (label_text, value) in enumerate(data_map.items()):
                ctk.CTkLabel(self.details_frame, text=label_text, font=ctk.CTkFont(weight="bold")).grid(
                    row=i, column=0, padx=10, pady=5, sticky="w"
                )
                ctk.CTkLabel(self.details_frame, text=value).grid(
                    row=i, column=1, padx=10, pady=5, sticky="w"
                )
        else:
            ctk.CTkLabel(self.details_frame, text="Producto no encontrado.", text_color="red").grid(
                row=0, column=0, columnspan=2, padx=10, pady=20
            )

    def go_back(self):
        """Regresa a la página de inventario."""
        self.master.master.show_page("inventario")
        
# --- CLASE DE VISTA: INVENTARIO ---

class InventarioPage(ctk.CTkFrame):
    """Contenido del Módulo de Inventario con cálculo de stock."""
    def __init__(self, master, db_manager):
        super().__init__(master, corner_radius=0)
        self.db_manager = db_manager
        
        self.grid_columnconfigure(0, weight=1)
        
        # Variables de control
        self.inventario_data = [] 
        self.filtered_data = [] 
        self.items_per_page = 15
        self.current_page = 1
        self.total_pages = 0
        
        # Título y Subtítulo
        ctk.CTkLabel(self, text="INVENTARIO", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, padx=0, pady=(0, 5), sticky="w"
        )
        ctk.CTkLabel(self, text="Stock de productos", font=ctk.CTkFont(size=16)).grid(
            row=1, column=0, padx=0, pady=(0, 20), sticky="w"
        )
        
        # --- Controles (Filtro, Alerta y Paginación) ---
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.controls_frame.grid_columnconfigure(0, weight=1)
        self.controls_frame.grid_columnconfigure(1, weight=1)

        # Marco Izquierdo (Búsqueda)
        self.search_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, sticky="w")
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Buscar código, producto, categoría o laboratorio...", width=300)
        self.search_entry.grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.search_entry.bind("<KeyRelease>", self.filter_inventory) 

        # Marco Derecho (Alerta y Paginación)
        self.alert_pag_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.alert_pag_frame.grid(row=0, column=1, sticky="e")
        
        # Select de Alerta
        ctk.CTkLabel(self.alert_pag_frame, text="Filtrar Alerta:").grid(row=0, column=0, padx=(10, 5), sticky="w")
        self.alert_options = ["Todos", "Stock bajo", "Sin stock"]
        self.combo_alerta = ctk.CTkComboBox(
            self.alert_pag_frame, 
            values=self.alert_options, 
            command=self.filter_inventory,
            width=120,
            state="readonly"
        )
        self.combo_alerta.set("Todos")
        self.combo_alerta.grid(row=0, column=1, padx=(0, 20), sticky="w")
        
        # Paginación (Se redibuja en draw_pagination_controls)
        self.pagination_frame = ctk.CTkFrame(self.alert_pag_frame, fg_color="transparent")
        self.pagination_frame.grid(row=0, column=2, sticky="e")
        
        # --- Marco Contenedor con Scroll Vertical ---
        self.table_scroll_container = ctk.CTkScrollableFrame(
            self, 
            label_text="Inventario de Productos", 
            label_font=ctk.CTkFont(weight="bold"), 
            orientation="vertical" 
        )
        self.table_scroll_container.grid(row=3, column=0, sticky="nsew")
        self.grid_rowconfigure(3, weight=1) 
        
        # Marco interno (Grid) para la tabla. Este marco tendrá un ancho fijo.
        self.table_grid_frame = ctk.CTkFrame(self.table_scroll_container, fg_color="transparent")
        self.table_grid_frame.grid(row=0, column=0, sticky="nsw") 
        
        # Cargar datos iniciales
        self.load_inventory_data()
        self.filter_inventory()
        
    def load_inventory_data(self):
        """Carga todos los datos de inventario con stock calculado."""
        self.inventario_data = self.db_manager.obtener_datos_inventario()

    def get_status_and_color(self, stock):
        """Determina el estado y el color de fondo de la fila."""
        stock = int(stock)
        if stock == 0:
            # 🔴 Caso 1: Sin Stock (Stock actual es CERO)
            return "Sin stock", "red" 
        elif stock <= STOCK_MINIMO:
            # 🟡 Caso 2: Stock bajo (Mayor que 0, pero menor o igual al mínimo)
            return "Stock bajo", "yellow" 
        elif stock >= STOCK_MINIMO:
            # 🟢 Caso 3: Normal (Stock actual mayor al mínimo)
            return "Normal", "green"

    def filter_inventory(self, event=None):
        """Filtra la lista de inventario basándose en el texto de búsqueda y la alerta."""
        search_term = self.search_entry.get().strip().lower()
        alert_filter = self.combo_alerta.get()
        
        # 1. Aplicar filtro de búsqueda general
        temp_data = []
        for row in self.inventario_data:
            text_to_search = f"{row[1]} {row[2]} {row[3]} {row[4]}".lower()
            if search_term in text_to_search:
                temp_data.append(row)
                
        # 2. Aplicar filtro de alerta
        self.filtered_data = []
        for row in temp_data:
            stock = row[5]
            status, _ = self.get_status_and_color(stock)
            
            if alert_filter == "Todos":
                self.filtered_data.append(row)
            elif alert_filter == "Stock bajo" and status == "Stock bajo":
                self.filtered_data.append(row)
            elif alert_filter == "Sin stock" and status == "Sin stock":
                self.filtered_data.append(row)
            
        # 3. Reiniciar y dibujar
        self.current_page = 1
        self.draw_inventory_table()
        self.draw_pagination_controls()

    def draw_inventory_table(self):
        """Dibuja la tabla de inventario con los datos paginados."""
        # Limpiar el marco de la tabla (self.table_grid_frame)
        for widget in self.table_grid_frame.winfo_children():
            widget.destroy()

        # Configuración de columnas (Anchos generosos para asegurar visibilidad)
        # Código, Producto, Categoría, Laboratorio, Stock Act., Stock Min., Estado, Acciones
        column_widths = [60, 230, 170, 170, 50, 50, 70, 150] 
        
        # 💥 CLAVE: Calcular el ancho total de la tabla (incluyendo padding)
        # 8 columnas * 10 de padding horizontal total por celda = 80px extra
        # Se agrega un margen adicional para la barra de scroll vertical si aparece
        TOTAL_WIDTH = sum(column_widths) + (len(column_widths) * 10) + 30 

        # Aplicar el ancho total al marco de la cuadrícula
        # Esto fuerza al CTkScrollableFrame a mostrar la barra de scroll horizontal 
        self.table_grid_frame.configure(width=TOTAL_WIDTH)
        self.table_grid_frame.grid_propagate(False) # Evita que el marco se encoja
        
        # --- Cabecera de la Tabla ---
        headers = ["Código", "Producto", "Categoría", "Laboratorio", "Stock Act.", f"Stock Min.", "Estado", "Acciones"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                self.table_grid_frame, 
                text=header, 
                font=ctk.CTkFont(weight="bold"), 
                width=column_widths[i]
            )
            # El padding en la derecha del último elemento ayuda a que el scrollbar no tape el contenido.
            padx_val = (5, 5) if i < len(headers) - 1 else (5, 10) 
            label.grid(row=0, column=i, padx=padx_val, pady=5, sticky="w")
            
            # 💡 CLAVE: Aplicar el peso para que las columnas se expandan
            # Aunque tenemos un ancho fijo, esto ayuda a la distribución interna.
            self.table_grid_frame.grid_columnconfigure(i, weight=1)

        # --- Paginación y Datos a Mostrar ---
        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        
        data_to_display = self.filtered_data[start_index:end_index]
        
        if not data_to_display:
            no_data_label = ctk.CTkLabel(self.table_grid_frame, text="No se encontraron productos en el inventario.", fg_color="transparent")
            no_data_label.grid(row=1, column=0, columnspan=len(headers), pady=10)
            return

        # --- Filas de Datos ---
        for i, row_data in enumerate(data_to_display):
            producto_id, codigo, nombre, categoria, laboratorio, stock_actual = row_data
            
            # 1. Determinar el estado y el color de fondo
            estado, color_key = self.get_status_and_color(stock_actual)
            
            color_map = {
                "green": "#0C9E38",  
                "yellow": "#DCA501", 
                "red": "#D91414",    
            }
            row_color = color_map.get(color_key, "transparent")
            
            row = i + 1  
            
            # 2. Dibujar las celdas de la fila
            cell_data = [codigo, nombre, categoria, laboratorio, stock_actual, STOCK_MINIMO, estado]
            for col_index, value in enumerate(cell_data):
                # Usar un CTkFrame como celda para aplicar el color de fondo y ancho
                cell_frame = ctk.CTkFrame(self.table_grid_frame, fg_color=row_color, height=30, width=column_widths[col_index])
                cell_frame.grid(row=row, column=col_index, padx=1, pady=1, sticky="nsew")
                cell_frame.grid_propagate(False) 
                cell_frame.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(cell_frame, text=str(value), fg_color=row_color).grid(
                    row=0, column=0, padx=5, sticky="w"
                )
            
            # 3. Columna Acciones (Botones)
            actions_frame = ctk.CTkFrame(self.table_grid_frame, fg_color=row_color, height=30, width=column_widths[7])
            actions_frame.grid(row=row, column=7, padx=1, pady=1, sticky="w")
            actions_frame.grid_propagate(False) 
            
            # Botón Ver
            btn_view = ctk.CTkButton(
                actions_frame, 
                text="Ver", 
                width=40,
                command=lambda id=producto_id: self.master.master.show_product_details(id)
            )
            btn_view.grid(row=0, column=0, padx=(5, 5))
            
            # Botón Eliminar
            btn_delete = ctk.CTkButton(
                actions_frame, 
                text="Eliminar", 
                width=40,
                fg_color="red",
                hover_color="darkred",
                command=lambda id=producto_id, name=nombre: self.delete_product(id, name)
            )
            btn_delete.grid(row=0, column=1)

    # --- Lógica de Paginación ---

    def draw_pagination_controls(self):
        for widget in self.pagination_frame.winfo_children():
            widget.destroy()

        total_items = len(self.filtered_data)
        self.total_pages = (total_items + self.items_per_page - 1) // self.items_per_page
        
        if self.total_pages <= 1:
            return 

        btn_prev = ctk.CTkButton(
            self.pagination_frame, 
            text="<", 
            width=30, 
            command=self.prev_page,
            state="normal" if self.current_page > 1 else "disabled"
        )
        btn_prev.grid(row=0, column=0, padx=(0, 5))

        page_label = ctk.CTkLabel(
            self.pagination_frame, 
            text=f"Página {self.current_page} de {self.total_pages}"
        )
        page_label.grid(row=0, column=1, padx=5)

        btn_next = ctk.CTkButton(
            self.pagination_frame, 
            text=">", 
            width=30, 
            command=self.next_page,
            state="normal" if self.current_page < self.total_pages else "disabled"
        )
        btn_next.grid(row=0, column=2, padx=(5, 0))

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.draw_inventory_table()
            self.draw_pagination_controls()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.draw_inventory_table()
            self.draw_pagination_controls()

    # --- Lógica de Acciones (Eliminar y Refrescar) ---
    
    def delete_product(self, product_id, product_name):
        """Elimina un producto y sus movimientos asociados."""
        if messagebox.askyesno("Confirmar Eliminación", f"¡ADVERTENCIA! ¿Está seguro de que desea eliminar el producto '{product_name}'? Se eliminarán también todos los movimientos asociados."):
            if self.db_manager.eliminar_producto_completo(product_id):
                messagebox.showinfo("Éxito", f"Producto '{product_name}' y todos sus movimientos han sido eliminados con éxito.")
                self.refresh_and_redraw()
            else:
                messagebox.showerror("Error", "Ocurrió un error al eliminar el producto.")
                
    def refresh_and_redraw(self):
        """Recarga los datos y redibuja la tabla y los controles."""
        self.load_inventory_data()
        self.filter_inventory() 

# --- CLASES DE VISTA: CATEGORÍAS Y PRODUCTOS ---

class CategoriasPage(ctk.CTkFrame):
    def __init__(self, master, db_manager):
        super().__init__(master, corner_radius=0)
        self.db_manager = db_manager
        
        self.grid_columnconfigure(0, weight=1)

        self.categorias_data = [] 
        self.items_per_page = 10
        self.current_page = 1
        self.total_pages = 0
        
        self.title_label = ctk.CTkLabel(self, text="CATEGORÍAS", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=0, pady=(0, 5), sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(self, text="Registro de categorías", font=ctk.CTkFont(size=16))
        self.subtitle_label.grid(row=1, column=0, padx=0, pady=(0, 15), sticky="w")

        self.btn_add_categoria = ctk.CTkButton(self, text="Agregar Categoría", command=self.open_add_category_modal)
        self.btn_add_categoria.grid(row=2, column=0, padx=0, pady=(0, 20), sticky="w")

        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.controls_frame.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(self.controls_frame, placeholder_text="Buscar categoría por nombre...")
        self.search_entry.grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.search_entry.bind("<KeyRelease>", self.filter_categories) 
        
        self.pagination_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.pagination_frame.grid(row=0, column=1, sticky="e")
        
        self.table_frame = ctk.CTkScrollableFrame(self, label_text="Lista de Categorías")
        self.table_frame.grid(row=4, column=0, sticky="nsew")
        self.grid_rowconfigure(4, weight=1) 
        
        self.load_categories_data()
        self.filtered_data = self.categorias_data
        self.draw_category_table()
        self.draw_pagination_controls()

    def load_categories_data(self):
        self.categorias_data = self.db_manager.obtener_categorias()
        
    def draw_category_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        column_widths = [50, 250, 100]  
        headers = ["N°", "Nombre de la Categoría", "Acciones"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(self.table_frame, text=header, font=ctk.CTkFont(weight="bold"), width=column_widths[i])
            label.grid(row=0, column=i, padx=(5, 15) if i == 2 else 5, pady=5, sticky="w")

        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        data_to_display = self.filtered_data[start_index:end_index]
        
        if not data_to_display:
            ctk.CTkLabel(self.table_frame, text="No hay categorías registradas.", fg_color="transparent").grid(row=1, column=0, columnspan=3, pady=10)
            return

        for i, (id, nombre) in enumerate(data_to_display):
            row = i + 1  
            num_display = start_index + i + 1 
            
            ctk.CTkLabel(self.table_frame, text=str(num_display)).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            ctk.CTkLabel(self.table_frame, text=nombre).grid(row=row, column=1, padx=5, pady=5, sticky="w")
            
            actions_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            actions_frame.grid(row=row, column=2, padx=5, pady=5, sticky="w")
            
            btn_edit = ctk.CTkButton(actions_frame, text="Editar", width=40, command=lambda id=id, name=nombre: self.open_edit_category_modal(id, name))
            btn_edit.grid(row=0, column=0, padx=(0, 5))
            
            btn_delete = ctk.CTkButton(actions_frame, text="Eliminar", width=40, fg_color="red", hover_color="darkred", command=lambda id=id, name=nombre: self.delete_category(id, name))
            btn_delete.grid(row=0, column=1)

    def filter_categories(self, event=None):
        search_term = self.search_entry.get().strip().lower()

        if not search_term:
            self.filtered_data = self.categorias_data
        else:
            self.filtered_data = [(id, nombre) for id, nombre in self.categorias_data if search_term in nombre.lower()]
            
        self.current_page = 1
        self.draw_category_table()
        self.draw_pagination_controls()

    def draw_pagination_controls(self):
        for widget in self.pagination_frame.winfo_children():
            widget.destroy()

        total_items = len(self.filtered_data)
        self.total_pages = (total_items + self.items_per_page - 1) // self.items_per_page
        
        if self.total_pages <= 1:
            return

        btn_prev = ctk.CTkButton(self.pagination_frame, text="<", width=30, command=self.prev_page, state="normal" if self.current_page > 1 else "disabled")
        btn_prev.grid(row=0, column=0, padx=(0, 5))

        page_label = ctk.CTkLabel(self.pagination_frame, text=f"Página {self.current_page} de {self.total_pages}")
        page_label.grid(row=0, column=1, padx=5)

        btn_next = ctk.CTkButton(self.pagination_frame, text=">", width=30, command=self.next_page, state="normal" if self.current_page < self.total_pages else "disabled")
        btn_next.grid(row=0, column=2, padx=(5, 0))

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.draw_category_table()
            self.draw_pagination_controls()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.draw_category_table()
            self.draw_pagination_controls()

    def open_add_category_modal(self):
        AddEditCategoryModal(self.master.master, "Registrar Categoría", self.register_category)

    def open_edit_category_modal(self, category_id, current_name):
        def update_func(name):
            self.update_category(category_id, name)
            
        AddEditCategoryModal(self.master.master, "Editar Categoría", update_func, current_name)

    def register_category(self, name):
        if not name:
            messagebox.showerror("Error", "El nombre de la categoría no puede estar vacío.")
            return False

        result = self.db_manager.insertar_categoria(name)

        if result == "DUPLICATE":
            messagebox.showerror("Error", f"La categoría '{name}' ya existe.")
            return False
        elif result is not None:
            messagebox.showinfo("Éxito", f"Categoría '{name}' registrada con éxito.")
            self.refresh_and_redraw()
            return True
        else:
            messagebox.showerror("Error", "Ocurrió un error al registrar la categoría.")
            return False

    def update_category(self, id, new_name):
        if not new_name:
            messagebox.showerror("Error", "El nombre de la categoría no puede estar vacío.")
            return False

        result = self.db_manager.actualizar_categoria(id, new_name)

        if result == "DUPLICATE":
            messagebox.showerror("Error", f"La categoría '{new_name}' ya existe.")
            return False
        elif result:
            messagebox.showinfo("Éxito", f"Categoría actualizada a '{new_name}' con éxito.")
            self.refresh_and_redraw()
            return True
        else:
            messagebox.showerror("Error", "Ocurrió un error al actualizar la categoría.")
            return False

    def delete_category(self, id, name):
        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar la categoría '{name}'?"):
            if self.db_manager.eliminar_categoria(id):
                messagebox.showinfo("Éxito", f"Categoría '{name}' eliminada con éxito.")
                self.refresh_and_redraw()
            else:
                messagebox.showerror("Error", "Ocurrió un error al eliminar la categoría.")
                
    def refresh_and_redraw(self):
        self.load_categories_data()
        self.filter_categories() 


class ProductosPage(ctk.CTkFrame):
    def __init__(self, master, db_manager):
        super().__init__(master, corner_radius=0)
        self.db_manager = db_manager
        
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="PRODUCTOS", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=0, pady=(0, 5), sticky="w")
        ctk.CTkLabel(self, text="Registro de productos", font=ctk.CTkFont(size=16)).grid(row=1, column=0, padx=0, pady=(0, 20), sticky="w")
        
        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        self.form_frame.grid_columnconfigure((0, 1), weight=1)

        # 1. Código
        ctk.CTkLabel(self.form_frame, text="Código/Número:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.entry_codigo = ctk.CTkEntry(self.form_frame, placeholder_text="Ej: PROD001")
        self.entry_codigo.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # 2. Nombre del Producto
        ctk.CTkLabel(self.form_frame, text="Nombre del Producto:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_nombre = ctk.CTkEntry(self.form_frame, placeholder_text="Ej: Paracetamol 500mg")
        self.entry_nombre.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # 3. Categoría (ComboBox)
        ctk.CTkLabel(self.form_frame, text="Categoría:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.categories_names = self.db_manager.obtener_todas_categorias_combo()
        if not self.categories_names:
             self.categories_names = ["No hay categorías (Agregue una primero)"]
        
        self.combo_categoria = ctk.CTkComboBox(self.form_frame, values=self.categories_names, state="readonly")
        self.combo_categoria.set(self.categories_names[0]) 
        self.combo_categoria.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # 4. Laboratorio
        ctk.CTkLabel(self.form_frame, text="Laboratorio:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.entry_laboratorio = ctk.CTkEntry(self.form_frame, placeholder_text="Ej: Bayer")
        self.entry_laboratorio.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        # 5. Botón Registrar
        self.btn_registrar = ctk.CTkButton(self.form_frame, text="Registrar Producto", command=self.registrar_producto_action)
        self.btn_registrar.grid(row=4, column=0, columnspan=2, padx=10, pady=20, sticky="e")
        
    def registrar_producto_action(self):
        codigo = self.entry_codigo.get().strip()
        nombre = self.entry_nombre.get().strip()
        nombre_categoria = self.combo_categoria.get()
        laboratorio = self.entry_laboratorio.get().strip()
        
        if not all([codigo, nombre, laboratorio]) or nombre_categoria == "No hay categorías (Agregue una primero)":
            messagebox.showerror("Error de Datos", "Los datos ingresados no son correctos. Por favor vuelva a ingresar los datos correctamente.")
            return

        categoria_id = self.db_manager.obtener_id_categoria_por_nombre(nombre_categoria)
        
        if categoria_id is None:
            messagebox.showerror("Error", "Error: No se encontró el ID de la categoría seleccionada. Intente recargar.")
            return

        result = self.db_manager.insertar_producto(codigo, nombre, categoria_id, laboratorio)

        if result == "DUPLICATE_CODE":
            messagebox.showerror("Error de Registro", f"El código '{codigo}' ya está registrado para otro producto.")
        elif result is not None:
            messagebox.showinfo("Registro Exitoso", "El producto se registró exitosamente.")
            self._limpiar_campos()
            # Al registrar un producto, recargamos el Inventario si existe
            if "inventario" in self.master.master.pages:
                self.master.master.pages["inventario"].refresh_and_redraw()
        else:
            messagebox.showerror("Error", "Ocurrió un error desconocido al registrar el producto.")
            
    def _limpiar_campos(self):
        self.entry_codigo.delete(0, 'end')
        self.entry_nombre.delete(0, 'end')
        self.entry_laboratorio.delete(0, 'end')


class MovimientosPage(ctk.CTkFrame):
    def __init__(self, master, db_manager):
        super().__init__(master, corner_radius=0)
        self.db_manager = db_manager
        
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="MOVIMIENTOS", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, padx=0, pady=(0, 5), sticky="w"
        )
        ctk.CTkLabel(self, text="Registro de movimientos", font=ctk.CTkFont(size=16)).grid(
            row=1, column=0, padx=0, pady=(0, 20), sticky="w"
        )
        
        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        self.form_frame.grid_columnconfigure((0, 1), weight=1)

        # 1. Producto (Select/ComboBox)
        ctk.CTkLabel(self.form_frame, text="Producto:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.productos_data = self.db_manager.obtener_productos_combo()
        self.productos_nombres = [nombre for id, nombre in self.productos_data]
        
        if not self.productos_nombres:
             self.productos_nombres = ["No hay productos (Agregue uno primero)"]
        
        self.combo_producto = ctk.CTkComboBox(self.form_frame, values=self.productos_nombres, state="readonly")
        self.combo_producto.set(self.productos_nombres[0]) 
        self.combo_producto.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # 2. Fecha
        ctk.CTkLabel(self.form_frame, text="Fecha (dd/mm/aaaa):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_fecha = ctk.CTkEntry(self.form_frame, placeholder_text="dd/mm/aaaa")
        self.entry_fecha.insert(0, date.today().strftime("%d/%m/%Y")) 
        self.entry_fecha.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # 3. Tipo de Movimiento
        ctk.CTkLabel(self.form_frame, text="Tipo de Movimiento:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.tipos_movimiento = ["Compra", "Venta"]
        self.combo_tipo = ctk.CTkComboBox(self.form_frame, values=self.tipos_movimiento, state="readonly")
        self.combo_tipo.set(self.tipos_movimiento[0])
        self.combo_tipo.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # 4. Precio Unitario
        ctk.CTkLabel(self.form_frame, text="Precio:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.entry_precio = ctk.CTkEntry(self.form_frame, placeholder_text="0.00")
        self.entry_precio.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # 5. Cantidad
        ctk.CTkLabel(self.form_frame, text="Cantidad (unidades):").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.entry_cantidad = ctk.CTkEntry(self.form_frame, placeholder_text="0")
        self.entry_cantidad.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        # 6. Observaciones
        ctk.CTkLabel(self.form_frame, text="Observaciones:").grid(row=5, column=0, padx=10, pady=5, sticky="nw")
        self.entry_observaciones = ctk.CTkTextbox(self.form_frame, height=80)
        self.entry_observaciones.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        
        # 7. Botón Registrar
        self.btn_registrar = ctk.CTkButton(self.form_frame, text="Registrar Movimiento", command=self.registrar_movimiento_action)
        self.btn_registrar.grid(row=6, column=0, columnspan=2, padx=10, pady=20, sticky="e")
        
    def registrar_movimiento_action(self):
        nombre_producto = self.combo_producto.get()
        fecha = self.entry_fecha.get().strip()
        tipo = self.combo_tipo.get()
        precio_str = self.entry_precio.get().strip()
        cantidad_str = self.entry_cantidad.get().strip()
        observaciones = self.entry_observaciones.get("1.0", "end-1c").strip()
        
        if nombre_producto == "No hay productos (Agregue uno primero)" or not all([fecha, tipo, precio_str, cantidad_str]):
            messagebox.showerror("Error de Datos", "Error: ingresa los datos correctamente. Asegúrate de seleccionar un producto y llenar todos los campos.")
            return
            
        try:
            date.strptime(fecha, "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Error de Datos", "Error: El formato de la fecha debe ser dd/mm/aaaa. Por favor, ingresa los datos correctamente.")
            return

        try:
            precio = float(precio_str)
            cantidad = int(cantidad_str)
            if precio <= 0 or cantidad <= 0:
                 raise ValueError("Los valores deben ser positivos.")
        except ValueError:
            messagebox.showerror("Error de Datos", "Error: Precio y Cantidad deben ser números positivos válidos. Por favor, ingresa los datos correctamente.")
            return

        producto_id = self.db_manager.obtener_id_producto_por_nombre(nombre_producto)
        
        if producto_id is None:
            messagebox.showerror("Error", "Error: No se encontró el ID del producto seleccionado. Intente recargar la aplicación.")
            return

        result = self.db_manager.insertar_movimiento(producto_id, fecha, tipo, precio, cantidad, observaciones)

        if result is not None:
            messagebox.showinfo("Registro Exitoso", "El movimiento se registró exitosamente.")
            self._limpiar_campos()
            # Al registrar un movimiento, recargamos el Inventario si existe
            if "inventario" in self.master.master.pages:
                self.master.master.pages["inventario"].refresh_and_redraw()
        else:
            messagebox.showerror("Error", "Ocurrió un error desconocido al registrar el movimiento. Verifica la integridad de los datos.")
            
    def _limpiar_campos(self):
        self.entry_precio.delete(0, 'end')
        self.entry_cantidad.delete(0, 'end')
        self.entry_observaciones.delete("1.0", "end")
        self.entry_fecha.delete(0, 'end')
        self.entry_fecha.insert(0, date.today().strftime("%d/%m/%Y"))


# --- CLASE PRINCIPAL DE LA APLICACIÓN ---

class App(ctk.CTk):
    """Contenedor principal con Navegación."""
    def __init__(self):
        super().__init__()

        self.db_manager = DBManager()
        
        self.title("Sistema de Inventario")
        self.geometry("1200x600") 
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.page_container = ctk.CTkFrame(self, corner_radius=0)
        self.page_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)
        
        self.current_page_view = None

        # --- 1. Navegador (Sidebar) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1) 
        
        ctk.CTkLabel(self.sidebar_frame, text="Inventario", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(20, 10)
        )
        
        self.btn_categorias = ctk.CTkButton(self.sidebar_frame, text="Categorías", command=lambda: self.show_page("categorias"))
        self.btn_categorias.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_productos = ctk.CTkButton(self.sidebar_frame, text="Productos", command=lambda: self.show_page("productos"))
        self.btn_productos.grid(row=2, column=0, padx=20, pady=10)
        
        self.btn_movimientos = ctk.CTkButton(self.sidebar_frame, text="Movimientos", command=lambda: self.show_page("movimientos"))
        self.btn_movimientos.grid(row=3, column=0, padx=20, pady=10)

        self.btn_inventario = ctk.CTkButton(self.sidebar_frame, text="Inventario", command=lambda: self.show_page("inventario"))
        self.btn_inventario.grid(row=4, column=0, padx=20, pady=10)
        
        # Inicializar todas las páginas
        self.pages = {
            "categorias": CategoriasPage(self.page_container, self.db_manager),
            "productos": ProductosPage(self.page_container, self.db_manager),
            "movimientos": MovimientosPage(self.page_container, self.db_manager),
            "inventario": InventarioPage(self.page_container, self.db_manager), 
        }

        self.show_page("inventario") 

    def show_page(self, page_name):
        """Muestra la página seleccionada y oculta las demás."""
        
        self.btn_categorias.configure(state="normal")
        self.btn_productos.configure(state="normal")
        self.btn_movimientos.configure(state="normal")
        self.btn_inventario.configure(state="normal") 
        
        if page_name.startswith("ver_producto"):
            if self.current_page_view:
                self.current_page_view.grid_forget()
            
            self.btn_inventario.configure(state="disabled")
            return 
        
        page_to_show = self.pages.get(page_name)
        
        if self.current_page_view:
            self.current_page_view.grid_forget()
            
        page_to_show.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.current_page_view = page_to_show
        
        if page_name == "categorias":
            self.btn_categorias.configure(state="disabled")
        elif page_name == "productos":
            self.btn_productos.configure(state="disabled")
        elif page_name == "movimientos":
            self.btn_movimientos.configure(state="disabled")
        elif page_name == "inventario":
            self.btn_inventario.configure(state="disabled")

    def show_product_details(self, product_id):
        """Muestra la vista de detalles de un producto específico."""
        
        if self.current_page_view:
            self.current_page_view.grid_forget()

        self.current_page_view = VerProductoPage(self.page_container, self.db_manager, product_id, self.pages["inventario"])
        self.current_page_view.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        self.btn_categorias.configure(state="normal")
        self.btn_productos.configure(state="normal")
        self.btn_movimientos.configure(state="normal")
        self.btn_inventario.configure(state="disabled") 


# Ejecución de la aplicación
if __name__ == "__main__":
    app = App()
    app.mainloop()