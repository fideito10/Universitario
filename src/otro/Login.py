import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os

class LoginPage:
    def __init__(self, root):
        self.root = root
        self.root.title("Club Argentino de Rugby - Login")
        self.root.geometry("800x600")
        self.root.configure(bg='#2E4057')  # Azul oscuro corporativo
        
        # Centrar la ventana en la pantalla
        self.center_window()
        
        # Crear el frame principal
        self.create_main_frame()
        
    def center_window(self):
        """Centrar la ventana en la pantalla"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_main_frame(self):
        """Crear el frame principal con todos los elementos"""
        
        # Frame superior para el logo
        top_frame = tk.Frame(self.root, bg='#2E4057', height=100)
        top_frame.pack(fill='x', padx=20, pady=(20, 0))
        top_frame.pack_propagate(False)
        
        # Logo (placeholder - aquí puedes agregar tu logo)
        logo_frame = tk.Frame(top_frame, bg='#2E4057')
        logo_frame.pack(side='right', padx=(0, 20), pady=10)
        
        # Placeholder para el logo
        logo_label = tk.Label(logo_frame, text="🏉 LOGO", font=("Arial", 16, "bold"), 
                             bg='#2E4057', fg='white', relief='solid', bd=2, padx=10, pady=5)
        logo_label.pack()
        
        # Frame central para el contenido principal
        center_frame = tk.Frame(self.root, bg='#2E4057')
        center_frame.pack(expand=True, fill='both', padx=50, pady=20)
        
        # Título principal
        title_label = tk.Label(center_frame, text="CLUB ARGENTINO DE RUGBY", 
                              font=("Arial", 28, "bold"), bg='#2E4057', fg='white')
        title_label.pack(pady=(40, 10))
        
        # Subtítulo
        subtitle_label = tk.Label(center_frame, text="Digitalización de los Clubes", 
                                 font=("Arial", 16, "italic"), bg='#2E4057', fg='#A8BFC8')
        subtitle_label.pack(pady=(0, 40))
        
        # Frame para el formulario de login
        login_frame = tk.Frame(center_frame, bg='white', relief='raised', bd=2)
        login_frame.pack(pady=20, padx=100, fill='x')
        
        # Título del formulario
        form_title = tk.Label(login_frame, text="Iniciar Sesión", 
                             font=("Arial", 20, "bold"), bg='white', fg='#2E4057')
        form_title.pack(pady=(30, 20))
        
        # Campo de usuario
        user_frame = tk.Frame(login_frame, bg='white')
        user_frame.pack(pady=10, padx=40, fill='x')
        
        user_label = tk.Label(user_frame, text="Usuario:", font=("Arial", 12, "bold"), 
                             bg='white', fg='#2E4057')
        user_label.pack(anchor='w')
        
        self.user_entry = tk.Entry(user_frame, font=("Arial", 12), relief='solid', bd=1, 
                                  bg='#F8F9FA', width=30)
        self.user_entry.pack(fill='x', pady=(5, 0), ipady=5)
        
        # Campo de contraseña
        pass_frame = tk.Frame(login_frame, bg='white')
        pass_frame.pack(pady=10, padx=40, fill='x')
        
        pass_label = tk.Label(pass_frame, text="Contraseña:", font=("Arial", 12, "bold"), 
                             bg='white', fg='#2E4057')
        pass_label.pack(anchor='w')
        
        self.pass_entry = tk.Entry(pass_frame, font=("Arial", 12), relief='solid', bd=1, 
                                  bg='#F8F9FA', show="*", width=30)
        self.pass_entry.pack(fill='x', pady=(5, 0), ipady=5)
        
        # Botones
        button_frame = tk.Frame(login_frame, bg='white')
        button_frame.pack(pady=30, padx=40, fill='x')
        
        # Botón de login
        login_button = tk.Button(button_frame, text="INGRESAR", font=("Arial", 12, "bold"), 
                                bg='#28A745', fg='white', relief='flat', bd=0, padx=30, pady=10,
                                command=self.login, cursor='hand2')
        login_button.pack(side='left', padx=(0, 10))
        
        # Botón de limpiar
        clear_button = tk.Button(button_frame, text="LIMPIAR", font=("Arial", 12, "bold"), 
                                bg='#6C757D', fg='white', relief='flat', bd=0, padx=30, pady=10,
                                command=self.clear_fields, cursor='hand2')
        clear_button.pack(side='left')
        
        # Enlaces adicionales
        links_frame = tk.Frame(login_frame, bg='white')
        links_frame.pack(pady=(10, 30))
        
        forgot_link = tk.Label(links_frame, text="¿Olvidaste tu contraseña?", 
                              font=("Arial", 10, "underline"), bg='white', fg='#007BFF', 
                              cursor='hand2')
        forgot_link.pack()
        forgot_link.bind("<Button-1>", self.forgot_password)
        
        # Footer
        footer_frame = tk.Frame(self.root, bg='#2E4057')
        footer_frame.pack(side='bottom', fill='x', pady=(0, 20))
        
        footer_label = tk.Label(footer_frame, text="© 2025 Club Argentino de Rugby - Sistema de Gestión", 
                               font=("Arial", 10), bg='#2E4057', fg='#A8BFC8')
        footer_label.pack()
    
    def login(self):
        """Función para manejar el login"""
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Por favor, complete todos los campos")
            return
        
        # Aquí puedes agregar la lógica de autenticación
        # Por ahora, solo mostramos un mensaje de ejemplo
        if username == "admin" and password == "admin":
            messagebox.showinfo("Éxito", f"¡Bienvenido {username}!")
            # Aquí puedes abrir la ventana principal de la aplicación
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")
    
    def clear_fields(self):
        """Limpiar los campos del formulario"""
        self.user_entry.delete(0, tk.END)
        self.pass_entry.delete(0, tk.END)
        self.user_entry.focus()
    
    def forgot_password(self, event):
        """Función para manejar la recuperación de contraseña"""
        messagebox.showinfo("Recuperar Contraseña", 
                           "Contacte al administrador del sistema para recuperar su contraseña.\n\n"
                           "Email: admin@clubargentinorugby.com\n"
                           "Teléfono: (011) 4XXX-XXXX")

def main():
    """Función principal para ejecutar la aplicación"""
    root = tk.Tk()
    app = LoginPage(root)
    
    # Configurar el evento de cerrar ventana
    root.protocol("WM_DELETE_WINDOW", root.quit)
    
    # Enfocar el campo de usuario al iniciar
    root.after(100, lambda: app.user_entry.focus())
    
    # Ejecutar la aplicación
    root.mainloop()

if __name__ == "__main__":
    main()