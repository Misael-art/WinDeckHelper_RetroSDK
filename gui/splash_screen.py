import sys
import time
from PyQt5.QtWidgets import QApplication, QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QPainter, QFont, QColor, QLinearGradient, QPen, QBrush

class LoadingWorker(QThread):
    """Worker thread para simular o carregamento da aplicação"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.loading_steps = [
            ("Inicializando sistema...", 10),
            ("Carregando componentes...", 25),
            ("Verificando dependências...", 40),
            ("Configurando interface...", 60),
            ("Preparando ambiente...", 80),
            ("Finalizando carregamento...", 100)
        ]
    
    def run(self):
        for status, progress in self.loading_steps:
            self.status_updated.emit(status)
            self.progress_updated.emit(progress)
            time.sleep(0.8)  # Simula tempo de carregamento
        
        self.finished.emit()

class AnimatedSplashScreen(QSplashScreen):
    """Splash Screen customizada com animações"""
    
    def __init__(self):
        # Criar um pixmap personalizado
        pixmap = self.create_splash_pixmap()
        super().__init__(pixmap, Qt.WindowStaysOnTopHint)
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Configurar layout
        self.setup_ui()
        
        # Configurar worker thread
        self.worker = LoadingWorker()
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.status_updated.connect(self.update_status)
        self.worker.finished.connect(self.loading_finished)
        
        # Configurar animação de fade
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(500)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Timer para animação de pontos
        self.dots_timer = QTimer()
        self.dots_timer.timeout.connect(self.animate_dots)
        self.dots_timer.start(500)
        self.dots_count = 0
        
    def create_splash_pixmap(self):
        """Criar um pixmap personalizado para o splash screen"""
        width, height = 500, 350
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fundo com gradiente
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor(45, 45, 48))
        gradient.setColorAt(1, QColor(30, 30, 32))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(70, 70, 75), 2))
        painter.drawRoundedRect(0, 0, width, height, 15, 15)
        
        # Título
        painter.setPen(QColor(255, 255, 255))
        title_font = QFont("Arial", 24, QFont.Bold)
        painter.setFont(title_font)
        painter.drawText(50, 80, "Environment Dev Script")
        
        # Subtítulo
        subtitle_font = QFont("Arial", 12)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(180, 180, 180))
        painter.drawText(50, 110, "Sistema de Gerenciamento de Ambiente de Desenvolvimento")
        
        # Logo/Ícone (círculo decorativo)
        painter.setBrush(QBrush(QColor(0, 120, 215)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(width - 100, 30, 60, 60)
        
        painter.end()
        return pixmap
    
    def setup_ui(self):
        """Configurar elementos da interface"""
        # Widget principal
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(50, 150, 50, 50)
        
        # Label de status
        self.status_label = QLabel("Inicializando...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 8px;
                text-align: center;
                background-color: #333;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0078d4, stop:1 #106ebe);
                border-radius: 6px;
            }
        """)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        
        # Label de versão
        version_label = QLabel("v2.0 - PyQt5 Enhanced")
        version_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 10px;
                background: transparent;
            }
        """)
        version_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(version_label)
        
        # Não podemos usar setWidget em QSplashScreen, então vamos posicionar manualmente
        widget.setParent(self)
        widget.move(0, 0)
        widget.resize(self.size())
        
    def update_progress(self, value):
        """Atualizar barra de progresso"""
        self.progress_bar.setValue(value)
        
    def update_status(self, status):
        """Atualizar texto de status"""
        self.status_label.setText(status)
        
    def animate_dots(self):
        """Animar pontos no texto de status"""
        current_text = self.status_label.text()
        if current_text.endswith("..."):
            base_text = current_text[:-3]
        elif current_text.endswith(".."):
            base_text = current_text[:-2]
        elif current_text.endswith("."):
            base_text = current_text[:-1]
        else:
            base_text = current_text
            
        self.dots_count = (self.dots_count + 1) % 4
        dots = "." * self.dots_count
        self.status_label.setText(base_text + dots)
        
    def loading_finished(self):
        """Chamado quando o carregamento termina"""
        self.dots_timer.stop()
        self.status_label.setText("Carregamento concluído!")
        
        # Fade out
        QTimer.singleShot(1000, self.fade_out)
        
    def fade_out(self):
        """Animação de fade out"""
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.finished.connect(self.close)
        self.opacity_animation.start()
        
    def start_loading(self):
        """Iniciar o processo de carregamento"""
        self.worker.start()
        
    def showEvent(self, event):
        """Evento chamado quando o splash é exibido"""
        super().showEvent(event)
        # Fade in
        self.setWindowOpacity(0.0)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()
        
        # Iniciar carregamento após um pequeno delay
        QTimer.singleShot(500, self.start_loading)

def show_splash_screen():
    """Função para exibir o splash screen"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    splash = AnimatedSplashScreen()
    splash.show()
    
    # Processar eventos para mostrar o splash
    app.processEvents()
    
    return splash

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    splash = AnimatedSplashScreen()
    splash.show()
    
    # Simular aplicação principal
    def close_splash():
        splash.close()
        app.quit()
    
    splash.worker.finished.connect(lambda: QTimer.singleShot(2000, close_splash))
    
    sys.exit(app.exec_())