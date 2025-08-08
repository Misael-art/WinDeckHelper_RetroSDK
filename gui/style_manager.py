"""style_manager.py
Applies a cohesive dark theme across all Tkinter ttk widgets for Environment Dev.
"""
from tkinter import ttk

# Core palette (can be adjusted centrally)
PRIMARY_COLOR = "#2196F3"  # Light blue
BACKGROUND_COLOR = "#2B2B2B"  # Window background
SURFACE_COLOR = "#3C3F41"  # Frames / surfaces
TEXT_COLOR = "#E0E0E0"
SUCCESS_COLOR = "#4CAF50"
ERROR_COLOR = "#F44336"
WARNING_COLOR = "#FF9800"

FONT_FAMILY = "Segoe UI"


def apply_theme(root):
    """Apply the custom EnvDevDark ttk style to a given Tk root or Toplevel."""
    style = ttk.Style(master=root)

    # Prefer clam as base (good cross-platform ttk theme)
    try:
        style.theme_use("clam")
    except Exception:
        pass  # fallback to current default if clam unavailable

    # Configure base colors
    style.configure("EnvDevDark.TFrame", background=SURFACE_COLOR)
    style.configure("EnvDevDark.TLabel", background=SURFACE_COLOR, foreground=TEXT_COLOR, font=(FONT_FAMILY, 12))
    style.configure("EnvDevDark.Title.TLabel", background=SURFACE_COLOR, foreground=TEXT_COLOR, font=(FONT_FAMILY, 18, "bold"))

    # Buttons
    style.configure(
        "EnvDevDark.TButton",
        background=PRIMARY_COLOR,
        foreground="white",
        relief="flat",
        borderwidth=0,
        font=(FONT_FAMILY, 10, "bold"),
        padding=6,
    )
    style.map(
        "EnvDevDark.TButton",
        background=[("active", "#1E88E5"), ("disabled", "#555555")],
        foreground=[("disabled", "#AAAAAA")],
    )

    # Accent (success etc.)
    style.configure("EnvDevDark.Success.TButton", background=SUCCESS_COLOR)
    style.map("EnvDevDark.Success.TButton", background=[("active", "#43A047")])

    # Progressbar
    style.configure(
        "EnvDevDark.Horizontal.TProgressbar",
        troughcolor=BACKGROUND_COLOR,
        bordercolor=BACKGROUND_COLOR,
        background=PRIMARY_COLOR,
        lightcolor=PRIMARY_COLOR,
        darkcolor=PRIMARY_COLOR,
    )

    # Notebook tabs
    style.configure(
        "EnvDevDark.TNotebook",
        background=SURFACE_COLOR,
        borderwidth=0,
    )
    style.configure(
        "EnvDevDark.TNotebook.Tab",
        background=SURFACE_COLOR,
        foreground=TEXT_COLOR,
        padding=(10, 5),
    )
    style.map(
        "EnvDevDark.TNotebook.Tab",
        background=[("selected", BACKGROUND_COLOR)],
        foreground=[("selected", PRIMARY_COLOR)],
    )

    # Apply background to root window as well
    root.configure(background=BACKGROUND_COLOR)

    # Make EnvDevDark default for generic widget classes when no style specified
    try:
        for widget in ("TFrame", "TLabel", "TButton", "Horizontal.TProgressbar", "TNotebook", "TNotebook.Tab"):
            try:
                style.element_create(f"EnvDevDark.{widget}", "from", widget)
                style.configure(widget, style="EnvDevDark." + widget)
            except Exception as e:
                # Skip widgets that don't exist in current theme
                print(f"Warning: Could not configure style for {widget}: {e}")
                continue
    except Exception as e:
        print(f"Warning: Theme configuration failed: {e}")