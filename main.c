#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <conio.h>
#include <ctype.h>

// Variabel tempat menyimpan data username dan password bawaan
char saved_username[50] = "luludd";
char saved_password[50] = "luludd123";

// Fungsi untuk membaca password dengan pilihan sensor
void input_password(char *password, int max_len, int sensor_aktif) {
    int i = 0;
    char ch;
    while (1) {
        ch = _getch(); // Membaca karakter satu per satu tanpa enter
        
        // Jika menekan tombol Enter
        if (ch == '\r' || ch == '\n') {
            break;
        } 
        // Jika menekan tombol Backspace (hapus karakter terakhir)
        else if (ch == '\b') {
            if (i > 0) {
                i--;
                printf("\b \b"); // Menghapus karakter di terminal
            }
        } 
        // Hanya menerima karakter yang bisa dicetak
        else if (isprint((unsigned char)ch)) {
            if (i < max_len - 1) {
                password[i] = ch;
                i++;
                if (sensor_aktif) {
                    printf("*"); // Tampilkan sensor bintang
                } else {
                    printf("%c", ch); // Tampilkan teks biasa (tidak disensor)
                }
            }
        }
    }
    password[i] = '\0'; // Menambahkan karakter null di akhir string
    printf("\n");
}

int main() {
    setbuf(stdout, NULL); // Menonaktifkan buffer stdout agar output langsung muncul
    int pilihan;
    char temp_username[50];
    char temp_password[50];
    int pilihan_sensor;

    while (1) {
        printf("\n===================================\n");
        printf("    SISTEM LOGIN SEDERHANA (CLI)   \n");
        printf("===================================\n");
        printf("1. Login (Masuk ke Sistem)\n");
        printf("2. Keluar\n");
        printf("Pilih Menu: ");
        
        if (scanf("%d", &pilihan) != 1) {
            while (getchar() != '\n'); // Bersihkan buffer jika input bukan angka
            printf("Input harus angka!\n");
            continue;
        }
        while (getchar() != '\n'); // Bersihkan sisa newline di buffer

        if (pilihan == 1) {
            // LOGIN USER
            printf("\n--- LOGIN SISTEM ---\n");
            printf("Masukkan Username: ");
            scanf("%49s", temp_username);
            while (getchar() != '\n');

            // Opsi untuk menyensor password
            printf("Aktifkan sensor password? (1 = Ya (Sensor Bintang), 0 = Tidak (Teks Biasa)): ");
            if (scanf("%d", &pilihan_sensor) != 1) {
                pilihan_sensor = 1;
            }
            while (getchar() != '\n');

            printf("Masukkan Password: ");
            input_password(temp_password, 50, pilihan_sensor);


            // Verifikasi Login terhadap data yang ada di variabel
            if (strcmp(saved_username, temp_username) == 0 &&
                strcmp(saved_password, temp_password) == 0) {
                printf("\n>>> LOGIN BERHASIL! Selamat datang, %s. <<<\n", temp_username);
            } else {
                printf("\n>>> LOGIN GAGAL! Username atau password salah. <<<\n");
            }

        } else if (pilihan == 2) {
            printf("Program selesai.\n");
            break;
        } else {
            printf("Menu tidak valid! Silakan masukkan pilihan 1-2.\n");
        }
    }

    return 0;
}
