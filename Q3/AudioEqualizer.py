import tkinter as tk
from tkinter import ttk, messagebox  # Added messagebox import
import numpy as np
from scipy.io import wavfile
from scipy import fft


class AudioEqualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Equalizer")
        self.fft_data = None  # Store FFT data

        # Input file section
        input_frame = ttk.Frame(root, padding="10")
        input_frame.grid(row=0, column=0, columnspan=9, sticky="ew")

        ttk.Label(input_frame, text="Audio File Name:").pack(side=tk.LEFT)
        self.input_file = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.input_file, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Load", command=self.load_audio).pack(side=tk.LEFT)

        # Equalizer sliders section
        slider_frame = ttk.Frame(root, padding="10")
        slider_frame.grid(row=1, column=0, columnspan=9)

        # Frequencies for each slider
        self.frequencies = ['63', '125', '250', '500', '1k', '2k', '4k', '8k', '16k']
        self.sliders = []

        for i, freq in enumerate(self.frequencies):
            frame = ttk.Frame(slider_frame)
            frame.grid(row=0, column=i, padx=10)

            slider = ttk.Scale(frame, from_=10, to=-10, length=200, orient='vertical')
            slider.set(0)
            slider.grid(row=0, column=0)
            self.sliders.append(slider)

            ttk.Label(frame, text=freq).grid(row=1, column=0)

        # Output file section
        output_frame = ttk.Frame(root, padding="10")
        output_frame.grid(row=2, column=0, columnspan=9, sticky="ew")

        ttk.Label(output_frame, text="Output File Name:").pack(side=tk.LEFT)
        self.output_file = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_file, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_frame, text="Process", command=self.process_audio).pack(side=tk.LEFT)

        # Message box
        message_frame = ttk.Frame(root, padding="10")
        message_frame.grid(row=3, column=0, columnspan=9)
        self.message_var = tk.StringVar()
        self.message_var.set("Status: Ready")
        ttk.Label(message_frame, textvariable=self.message_var, width=50).pack()

        # Exit button
        exit_frame = ttk.Frame(root, padding="10")
        exit_frame.grid(row=4, column=0, columnspan=9)
        ttk.Button(exit_frame, text="Exit", command=root.destroy).pack()

    def load_audio(self):
        try:
            # Read audio file
            sample_rate, audio_data = wavfile.read(self.input_file.get())

            # Convert to mono if stereo
            if len(audio_data.shape) > 1:
                audio_data = audio_data[:, 0]

            # Perform FFT
            self.fft_data = fft.fft(audio_data)
            self.sample_rate = sample_rate

            self.message_var.set("Status: Audio file loaded successfully!")

        except Exception as e:
            self.message_var.set(f"Error: Failed to load audio file - {str(e)}")
            messagebox.showerror("Error", f"Failed to load audio file: {str(e)}")

    def process_audio(self):
        if self.fft_data is None:
            self.message_var.set("Error: Please load an audio file first!")
            messagebox.showerror("Error", "Please load an audio file first!")
            return

        # Get slider values
        slider_values = [slider.get() for slider in self.sliders]

        try:
            # Call processing function
            process_audio_file(self.fft_data, slider_values, self.sample_rate, self.output_file.get())
            self.message_var.set("Status: Audio processed successfully!")
            messagebox.showinfo("Success", "Audio processed successfully!")

        except Exception as e:
            self.message_var.set(f"Error: Failed to process audio - {str(e)}")
            messagebox.showerror("Error", f"Failed to process audio: {str(e)}")


def process_audio_file(fft_data, slider_values, sample_rate, output_file):
    # Map slider values from [-10, 10] to scaling factors [0, 10]
    scale_factors = [max(0, (val + 10) / 2) for val in slider_values]

    # Compute FFT frequency bins
    N = len(fft_data)
    freqs = np.fft.fftfreq(N, d=1 / sample_rate)

    # Define fixed frequency bands
    bands = [(0, 63), (64, 125), (126, 250), (251, 500),
             (501, 1000), (1001, 2000), (2001, 4000),
             (4001, 8000), (8001, 16000)]

    # Apply the scaling factors to the FFT coefficients in each band
    fft_data_mod = fft_data.copy()
    for band, factor in zip(bands, scale_factors):
        indices = np.where((np.abs(freqs) >= band[0]) & (np.abs(freqs) <= band[1]))
        fft_data_mod[indices] *= factor

    # Compute inverse FFT to get the time-domain signal
    processed_signal = np.real(fft.ifft(fft_data_mod))

    # Normalize to prevent clipping when saving as 16-bit PCM
    processed_signal = processed_signal / np.max(np.abs(processed_signal)) * 32767
    processed_signal = processed_signal.astype(np.int16)

    # Save the processed audio file
    wavfile.write(output_file, sample_rate, processed_signal)


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioEqualizerApp(root)
    root.mainloop()
