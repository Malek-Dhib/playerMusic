import pygame
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QSlider, QMessageBox
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import os
from glob import glob

MUSIC_END_EVENT = pygame.USEREVENT + 1

class AudioPlayer(QWidget):
    music_ended = pyqtSignal()

    def __init__(self, music_directory):
        super().__init__()

        pygame.mixer.init()

        self.layout = QVBoxLayout()
        self.music_directory = music_directory
        self.current_index = 0
        self.paused = False
        self.looping = False
        self.user_changed_position = False
        self.loop_triggered = False
        self.volume = 0.5
        self.music_files = self.load_music_files()
        pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        self.paused_position = 0
        self.current_position = 0

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setMinimum(0)
        self.position_slider.setMaximum(100)
        self.position_slider.setValue(0)
        self.position_slider.sliderReleased.connect(self.handle_slider_release)
        self.layout.addWidget(self.position_slider)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_position_slider)
        self.update_timer.start(1000)

        self.init_ui()

    def load_music_files(self):
        music_files = glob(os.path.join(self.music_directory, '*.mp3')) + glob(os.path.join(self.music_directory, '*.wav'))
        return music_files

    def init_ui(self):
        self.setWindowTitle('Lecteur Audio')
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        self.status_label = QLabel('Aucun fichier sélectionné')
        layout.addWidget(self.status_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(int(self.volume * 100))
        self.volume_slider.valueChanged.connect(self.set_volume)
        layout.addWidget(self.volume_slider)

        self.play_button = QPushButton('Lire', self)
        self.play_button.clicked.connect(self.play_pause_audio)
        layout.addWidget(self.play_button)

        self.pause_button = QPushButton('Pause', self)
        self.pause_button.clicked.connect(self.pause_audio)
        layout.addWidget(self.pause_button)

        self.stop_button = QPushButton('Arrêter', self)
        self.stop_button.clicked.connect(self.stop_audio)
        layout.addWidget(self.stop_button)

        self.select_button = QPushButton('Changer de musique', self)
        self.select_button.clicked.connect(self.change_music)
        layout.addWidget(self.select_button)

        self.loop_button = QPushButton('Boucle', self)
        self.loop_button.clicked.connect(self.toggle_loop)
        layout.addWidget(self.loop_button)

        layout.addWidget(self.position_slider)

        if self.music_files:
            first_music_path = self.music_files[0]
            pygame.mixer.music.load(first_music_path)
            self.music_length = pygame.mixer.Sound(first_music_path).get_length()

        self.setLayout(layout)

    def update_position_slider(self):
        if pygame.mixer.music.get_busy():
            if not self.user_changed_position:
                position = pygame.mixer.music.get_pos() / 1000
                length = self.music_length
                if length > 0:
                    percentage = (position / length) * 100
                    self.position_slider.setValue(int(percentage))
            else:
                self.user_changed_position = False

    def play_pause_audio(self):
        if self.music_files:
            pygame.mixer.init()
            pygame.mixer.music.load(self.music_files[self.current_index])
            self.music_length = pygame.mixer.Sound(self.music_files[self.current_index]).get_length()
        else:
            self.show_message('Aucun fichier audio trouvé dans le répertoire.')

        if not pygame.mixer.music.get_busy():
            if not pygame.mixer.get_init():
                pygame.mixer.music.load(self.music_files[self.current_index])

            pygame.mixer.music.play(start=int(self.current_position / 1000))
            self.status_label.setText(f'Lecture en cours: {os.path.basename(self.music_files[self.current_index])}')
            self.loop_triggered = False
        else:
            if self.paused:
                pygame.mixer.music.unpause()
                self.status_label.setText(f'Lecture en cours: {os.path.basename(self.music_files[self.current_index])}')
            else:
                # Reprendre à la position actuelle
                pygame.mixer.music.set_pos(self.current_position / 1000)
                pygame.mixer.music.play()
                self.status_label.setText(f'Lecture en cours: {os.path.basename(self.music_files[self.current_index])}')

            self.paused = not self.paused
            self.loop_triggered = False
            loop_state = 'activée' if self.looping else 'désactivée'
            self.status_label.setText(f'Boucle {loop_state}')



    def pause_audio(self):
        if pygame.mixer.music.get_busy() and not self.loop_triggered:
            pygame.mixer.music.pause()
            self.status_label.setText('Lecture en pause')
            self.paused = True

    def stop_audio(self):
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            self.status_label.setText('Lecture arrêtée')
            self.paused = False
        else:
            self.show_message('Aucune piste audio en cours de lecture.')

    def change_music(self):
        self.current_index = (self.current_index + 1) % len(self.music_files)
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        new_music_path = self.music_files[self.current_index]
        new_music = pygame.mixer.Sound(new_music_path)
        self.music_length = new_music.get_length()

        pygame.mixer.music.load(new_music_path)
        pygame.mixer.music.play(-1 if self.looping else 0)
        self.status_label.setText(f'Nouvelle musique sélectionnée: {os.path.basename(new_music_path)}')
        self.loop_button.setEnabled(True)

    def handle_music_end(self, event):
        if event.type == MUSIC_END_EVENT and not self.user_changed_position:
            pygame.mixer.music.play(-1 if self.looping else 0)
            self.loop_triggered = True
            self.position_slider.setValue(0)

    def toggle_loop(self):
        self.looping = not self.looping
        loop_state = 'activée' if self.looping else 'désactivée'
        self.status_label.setText(f'Boucle {loop_state}')

    def set_volume(self):
        self.volume = self.volume_slider.value() / 100
        pygame.mixer.music.set_volume(self.volume)

    def show_message(self, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle('Avertissement')
        msg_box.setText(message)
        msg_box.exec_()

    def handle_slider_release(self):
        if pygame.mixer.music.get_busy():
            new_position = self.position_slider.value() / 100.0 * self.music_length
            pygame.mixer.music.set_pos(new_position)
            self.user_changed_position = True

if __name__ == '__main__':
    app = QApplication([])
    player = AudioPlayer('/Users/malek/Desktop/cv/Musique spotify/music')
    player.show()
    app.exec_()
