import customtkinter as ctk
from tkinter import messagebox
from db_manager import DBManager

# Configuración de CustomTkinter
ctk.set_appearance_mode("System")  # Modos: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    """Ventana principal de la aplicación."""
    def __init__(self):
        super().__init__()

        # Inicialización del gestor de base de datos
        self.db_manager = DBManager()
        self.categorias_data = [] # Para almacenar los datos de la tabla

        # Configuración de la ventana principal
        self.title("Sistema de Inventario - Categorías")
        self.geometry("800x600")
        
        # Grid layout (2x1) - Navegador a la izquierda y Contenido a la derecha
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- 1. Navegador (Sidebar) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Inventario", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Botones de navegación (simulados)
        self.btn_categorias = ctk.CTkButton(self.sidebar_frame, text="Categorías", state="disabled")
        self.btn_categorias.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_productos = ctk.CTkButton(self.sidebar_frame, text="Productos")
        self.btn_productos.grid(row=2, column=0, padx=20, pady=10)

        # --- 2. Contenido Principal: CATEGORÍAS ---
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        
        # Título y Subtítulo
        self.title_label = ctk.CTkLabel(self.main_content_frame, text="CATEGORÍAS", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=0, pady=(0, 5), sticky="w")
        
        self.subtitle_label = ctk.CTkLabel(self.main_content_frame, text="Registro de categorías", font=ctk.CTkFont(size=16))
        self.subtitle_label.grid(row=1, column=0, padx=0, pady=(0, 15), sticky="w")

        # Botón "Agregar Categoría"
        self.btn_add_categoria = ctk.CTkButton(
            self.main_content_frame, 
            text="Agregar Categoría", 
            command=self.open_add_category_modal
        )
        self.btn_add_categoria.grid(row=2, column=0, padx=0, pady=(0, 20), sticky="w")

        # --- 3. Filtro y Paginación (Controles superiores de la tabla) ---
        self.controls_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.controls_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.controls_frame.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(self.controls_frame, placeholder_text="Buscar categoría por nombre...")
        self.search_entry.grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.search_entry.bind("<KeyRelease>", self.filter_categories) # Filtrar al escribir
        
        # Paginación (Inicialmente vacío, se llena en load_table)
        self.pagination_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.pagination_frame.grid(row=0, column=1, sticky="e")
        
        # --- 4. Tabla de Categorías ---
        self.table_frame = ctk.CTkScrollableFrame(self.main_content_frame, label_text="Lista de Categorías")
        self.table_frame.grid(row=4, column=0, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(4, weight=1) # Para que la tabla se expanda
        
        
        # --- PARÁMETROS DE PAGINACIÓN Y FILTRO (CORREGIDO: MOVIDO ARRIBA) ---
        # **ESTO ES LO QUE SOLUCIONA EL ERROR 'AttributeError: ... has no attribute 'current_page'**
        self.items_per_page = 10
        self.current_page = 1
        self.total_pages = 0
        
        # Cargar los datos y dibujar la tabla
        self.load_categories_data()
        self.filtered_data = self.categorias_data # Inicialmente, datos filtrados = todos los datos
        self.draw_category_table()
        
        # Dibujar los controles de paginación (depende de self.total_pages)
        self.draw_pagination_controls()

    # ======================================================================
    # LÓGICA DE DATOS
    # ======================================================================
    
    def load_categories_data(self):
        """Carga todas las categorías desde la DB y actualiza la lista interna."""
        self.categorias_data = self.db_manager.obtener_categorias()
        # Nota: self.filtered_data ya no se redefine aquí para evitar sobrescribir si ya hay un filtro activo.
        
    def draw_category_table(self):
        """Dibuja la tabla de categorías con los datos paginados."""
        # Limpiar la tabla anterior
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        # Configuración de columnas (Anchos aproximados)
        column_widths = [50, 250, 100]  # Num, Nombre, Acciones
        
        # --- Cabecera de la Tabla ---
        headers = ["N°", "Nombre de la Categoría", "Acciones"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                self.table_frame, 
                text=header, 
                font=ctk.CTkFont(weight="bold"), 
                width=column_widths[i]
            )
            label.grid(row=0, column=i, padx=(5, 15) if i == 2 else 5, pady=5, sticky="w")

        # --- Paginación y Datos a Mostrar ---
        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        
        data_to_display = self.filtered_data[start_index:end_index]
        
        if not data_to_display:
            no_data_label = ctk.CTkLabel(self.table_frame, text="No hay categorías registradas.", fg_color="transparent")
            no_data_label.grid(row=1, column=0, columnspan=3, pady=10)
            return

        # --- Filas de Datos ---
        for i, (id, nombre) in enumerate(data_to_display):
            row = i + 1  # Fila 1 en la tabla (después de la cabecera)
            num_display = start_index + i + 1 # El número visible que comienza desde 1
            
            # Columna N°
            ctk.CTkLabel(self.table_frame, text=str(num_display)).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            
            # Columna Nombre
            ctk.CTkLabel(self.table_frame, text=nombre).grid(row=row, column=1, padx=5, pady=5, sticky="w")
            
            # Columna Acciones (Botones)
            actions_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            actions_frame.grid(row=row, column=2, padx=5, pady=5, sticky="w")
            
            # Botón Editar
            btn_edit = ctk.CTkButton(
                actions_frame, 
                text="Editar", 
                width=40,
                command=lambda id=id, name=nombre: self.open_edit_category_modal(id, name)
            )
            btn_edit.grid(row=0, column=0, padx=(0, 5))
            
            # Botón Eliminar
            btn_delete = ctk.CTkButton(
                actions_frame, 
                text="Eliminar", 
                width=40,
                fg_color="red",
                hover_color="darkred",
                command=lambda id=id, name=nombre: self.delete_category(id, name)
            )
            btn_delete.grid(row=0, column=1)

    # ======================================================================
    # LÓGICA DE FILTRO Y PAGINACIÓN
    # ======================================================================
    
    def filter_categories(self, event=None):
        """Filtra la lista de categorías basándose en el texto de búsqueda."""
        search_term = self.search_entry.get().strip().lower()
        
        if not search_term:
            self.filtered_data = self.categorias_data
        else:
            self.filtered_data = [
                (id, nombre) for id, nombre in self.categorias_data 
                if search_term in nombre.lower()
            ]
            
        # Reiniciar a la primera página con los nuevos datos filtrados
        self.current_page = 1
        self.draw_category_table()
        self.draw_pagination_controls()

    def draw_pagination_controls(self):
        """Dibuja los botones y etiquetas de paginación."""
        # Limpiar controles anteriores
        for widget in self.pagination_frame.winfo_children():
            widget.destroy()

        total_items = len(self.filtered_data)
        self.total_pages = (total_items + self.items_per_page - 1) // self.items_per_page
        
        if self.total_pages <= 1:
            return # No mostrar paginación si solo hay una página o menos

        # Botón Anterior
        btn_prev = ctk.CTkButton(
            self.pagination_frame, 
            text="<", 
            width=30, 
            command=self.prev_page,
            state="normal" if self.current_page > 1 else "disabled"
        )
        btn_prev.grid(row=0, column=0, padx=(0, 5))

        # Etiqueta de Página
        page_label = ctk.CTkLabel(
            self.pagination_frame, 
            text=f"Página {self.current_page} de {self.total_pages}"
        )
        page_label.grid(row=0, column=1, padx=5)

        # Botón Siguiente
        btn_next = ctk.CTkButton(
            self.pagination_frame, 
            text=">", 
            width=30, 
            command=self.next_page,
            state="normal" if self.current_page < self.total_pages else "disabled"
        )
        btn_next.grid(row=0, column=2, padx=(5, 0))

    def prev_page(self):
        """Va a la página anterior."""
        if self.current_page > 1:
            self.current_page -= 1
            self.draw_category_table()
            self.draw_pagination_controls()

    def next_page(self):
        """Va a la página siguiente."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.draw_category_table()
            self.draw_pagination_controls()

    # ======================================================================
    # LÓGICA DE MODAL DE REGISTRO/EDICIÓN
    # ======================================================================

    def open_add_category_modal(self):
        """Abre el modal para registrar una nueva categoría."""
        AddEditCategoryModal(self, "Registrar Categoría", self.register_category)

    def open_edit_category_modal(self, category_id, current_name):
        """Abre el modal para editar una categoría existente."""
        # Creamos una función lambda para pasar los argumentos adicionales a la función de guardado
        def update_func(name):
            self.update_category(category_id, name)
            
        AddEditCategoryModal(self, "Editar Categoría", update_func, current_name)


    def register_category(self, name):
        """Lógica para guardar la nueva categoría en la DB."""
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
        """Lógica para actualizar una categoría existente en la DB."""
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
        """Lógica para eliminar una categoría de la DB y de la tabla."""
        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar la categoría '{name}'?"):
            if self.db_manager.eliminar_categoria(id):
                messagebox.showinfo("Éxito", f"Categoría '{name}' eliminada con éxito.")
                self.refresh_and_redraw()
            else:
                messagebox.showerror("Error", "Ocurrió un error al eliminar la categoría.")
                
    def refresh_and_redraw(self):
        """Recarga los datos y redibuja la tabla y los controles."""
        # 1. Recargar datos de la DB
        self.load_categories_data() 
        # 2. Reaplicar filtro (para actualizar self.filtered_data y redibujar la tabla)
        self.filter_categories() 
        
class AddEditCategoryModal(ctk.CTkToplevel):
    """Modal (Ventana emergente) para agregar o editar categorías."""
    def __init__(self, master, title, save_command, initial_name=""):
        super().__init__(master)
        self.title(title)
        self.geometry("300x150")
        self.resizable(False, False)
        
        # Bloquear la ventana principal mientras el modal esté abierto
        self.transient(master) 
        self.grab_set() 

        self.save_command = save_command
        
        # Título del Modal
        self.label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        self.label.pack(pady=10)

        # Campo de entrada (Nombre de la categoría)
        self.entry_nombre = ctk.CTkEntry(self, placeholder_text="Nombre de la Categoría", width=250)
        self.entry_nombre.pack(pady=5)
        self.entry_nombre.insert(0, initial_name) # Precargar el nombre si es edición

        # Frame para los botones
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=10)
        
        # Botón Registrar / Guardar
        btn_registrar = ctk.CTkButton(self.button_frame, text="Registrar" if not initial_name else "Guardar", command=self.save_action, width=100)
        btn_registrar.grid(row=0, column=0, padx=5)
        
        # Botón Cancelar
        btn_cancelar = ctk.CTkButton(self.button_frame, text="Cancelar", command=self.destroy, fg_color="gray", hover_color="darkgray", width=100)
        btn_cancelar.grid(row=0, column=1, padx=5)

    def save_action(self):
        """Ejecuta el comando de guardado y cierra el modal si es exitoso."""
        nombre = self.entry_nombre.get().strip()
        if self.save_command(nombre):
            self.destroy()

# Ejecución de la aplicación
if __name__ == "__main__":
    app = App()
    app.mainloop()