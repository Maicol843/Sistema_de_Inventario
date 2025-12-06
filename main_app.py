import customtkinter as ctk
from tkinter import messagebox
from db_manager import DBManager
from datetime import date # Para obtener la fecha actual

# Configuración de CustomTkinter
ctk.set_appearance_mode("System")  # Modos: "System", "Dark", "Light"
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

# --- CLASE DE VISTA: CATEGORÍAS (Se mantiene) ---

class CategoriasPage(ctk.CTkFrame):
    """Contenido del Módulo de Categorías."""
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


# --- CLASE DE VISTA: PRODUCTOS ---

class ProductosPage(ctk.CTkFrame):
    """Contenido del Módulo de Productos."""
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
        else:
            messagebox.showerror("Error", "Ocurrió un error desconocido al registrar el producto.")
            
    def _limpiar_campos(self):
        self.entry_codigo.delete(0, 'end')
        self.entry_nombre.delete(0, 'end')
        self.entry_laboratorio.delete(0, 'end')


# --- CLASE DE VISTA: MOVIMIENTOS ---

class MovimientosPage(ctk.CTkFrame):
    """Contenido del Módulo de Movimientos (Compra/Venta)."""
    def __init__(self, master, db_manager):
        super().__init__(master, corner_radius=0)
        self.db_manager = db_manager
        
        self.grid_columnconfigure(0, weight=1)

        # Título y Subtítulo
        ctk.CTkLabel(self, text="MOVIMIENTOS", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, padx=0, pady=(0, 5), sticky="w"
        )
        ctk.CTkLabel(self, text="Registro de movimientos", font=ctk.CTkFont(size=16)).grid(
            row=1, column=0, padx=0, pady=(0, 20), sticky="w"
        )
        
        # --- Formulario de Registro de Movimiento ---
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

        # 2. Fecha (MODIFICADO: Usando formato dd/mm/aaaa)
        ctk.CTkLabel(self.form_frame, text="Fecha (dd/mm/aaaa):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_fecha = ctk.CTkEntry(self.form_frame, placeholder_text="dd/mm/aaaa")
        # --- CAMBIO DE FORMATO AQUÍ ---
        self.entry_fecha.insert(0, date.today().strftime("%d/%m/%Y")) 
        # ------------------------------
        self.entry_fecha.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # 3. Tipo de Movimiento (Select/ComboBox)
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
        """Recupera los datos del formulario y los inserta en la base de datos."""
        
        nombre_producto = self.combo_producto.get()
        fecha = self.entry_fecha.get().strip() # Se obtiene la fecha como dd/mm/aaaa
        tipo = self.combo_tipo.get()
        precio_str = self.entry_precio.get().strip()
        cantidad_str = self.entry_cantidad.get().strip()
        observaciones = self.entry_observaciones.get("1.0", "end-1c").strip()
        
        # 1. Validación inicial de campos llenos
        if nombre_producto == "No hay productos (Agregue uno primero)" or not all([fecha, tipo, precio_str, cantidad_str]):
            messagebox.showerror("Error de Datos", "Error: ingresa los datos correctamente. Asegúrate de seleccionar un producto y llenar todos los campos.")
            return
            
        # 2. Validación de formato de fecha simple (dd/mm/aaaa)
        try:
            # Intentamos convertir la fecha del formato dd/mm/aaaa a un objeto date
            fecha_obj = date.strptime(fecha, "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Error de Datos", "Error: El formato de la fecha debe ser dd/mm/aaaa. Por favor, ingresa los datos correctamente.")
            return

        # 3. Validación de números
        try:
            precio = float(precio_str)
            cantidad = int(cantidad_str)
            if precio <= 0 or cantidad <= 0:
                 raise ValueError("Los valores deben ser positivos.")
        except ValueError:
            messagebox.showerror("Error de Datos", "Error: Precio y Cantidad deben ser números positivos válidos. Por favor, ingresa los datos correctamente.")
            return

        # 4. Obtener el ID del producto
        producto_id = self.db_manager.obtener_id_producto_por_nombre(nombre_producto)
        
        if producto_id is None:
            messagebox.showerror("Error", "Error: No se encontró el ID del producto seleccionado. Intente recargar la aplicación.")
            return

        # 5. Insertar el movimiento (se inserta la fecha con el formato dd/mm/aaaa)
        result = self.db_manager.insertar_movimiento(producto_id, fecha, tipo, precio, cantidad, observaciones)

        if result is not None:
            messagebox.showinfo("Registro Exitoso", "El movimiento se registró exitosamente.")
            self._limpiar_campos()
        else:
            messagebox.showerror("Error", "Ocurrió un error desconocido al registrar el movimiento. Verifica la integridad de los datos.")
            
    def _limpiar_campos(self):
        """Limpia los campos del formulario tras un registro exitoso."""
        self.entry_precio.delete(0, 'end')
        self.entry_cantidad.delete(0, 'end')
        self.entry_observaciones.delete("1.0", "end")
        
        # --- CAMBIO DE FORMATO AQUÍ ---
        self.entry_fecha.delete(0, 'end')
        self.entry_fecha.insert(0, date.today().strftime("%d/%m/%Y"))
        # ------------------------------


# --- CLASE PRINCIPAL DE LA APLICACIÓN (Se mantiene) ---

class App(ctk.CTk):
    """Contenedor principal con Navegación."""
    def __init__(self):
        super().__init__()

        self.db_manager = DBManager()
        
        self.title("Sistema de Inventario")
        self.geometry("800x600")
        
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
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        
        ctk.CTkLabel(self.sidebar_frame, text="Inventario", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(20, 10)
        )
        
        self.btn_categorias = ctk.CTkButton(self.sidebar_frame, text="Categorías", command=lambda: self.show_page("categorias"))
        self.btn_categorias.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_productos = ctk.CTkButton(self.sidebar_frame, text="Productos", command=lambda: self.show_page("productos"))
        self.btn_productos.grid(row=2, column=0, padx=20, pady=10)
        
        self.btn_movimientos = ctk.CTkButton(self.sidebar_frame, text="Movimientos", command=lambda: self.show_page("movimientos"))
        self.btn_movimientos.grid(row=3, column=0, padx=20, pady=10)
        
        self.pages = {
            "categorias": CategoriasPage(self.page_container, self.db_manager),
            "productos": ProductosPage(self.page_container, self.db_manager),
            "movimientos": MovimientosPage(self.page_container, self.db_manager),
        }

        self.show_page("categorias")

    def show_page(self, page_name):
        """Muestra la página seleccionada y oculta las demás."""
        
        self.btn_categorias.configure(state="normal")
        self.btn_productos.configure(state="normal")
        self.btn_movimientos.configure(state="normal")
        
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


# Ejecución de la aplicación
if __name__ == "__main__":
    app = App()
    app.mainloop()