using System;
using System.IO;
using System.Drawing;
using System.Drawing.Imaging;
using System.Threading;
using LGIAiCamTD100ControlLib;

class IcamBridge
{
    // Directory Constants
    const string ENROLLMENT_DIR = @"C:\Users\kevin\Documents\iCAM TD100 SDK\Enrollment";
    const string RECOGNITION_DIR = @"C:\Users\kevin\Documents\iCAM TD100 SDK\Recognition";
    const string ICAM_FRAMES_DIR = @"C:\icam_frames";
    const string OUTPUT_BIN_RIGHT = @"C:\icam_frames\latest_R.bin";
    const string OUTPUT_BIN_LEFT = @"C:\icam_frames\latest_L.bin";
    const string READY_FILE = @"C:\icam_frames\ready.flag";

    const int WIDTH = 640;
    const int HEIGHT = 480;

    static IAiCamTD100ControlClass cam = new IAiCamTD100ControlClass();
    static volatile bool running = true;
    static int frameCount = 0;

    static string mode = "recognize";
    static string saveDir = "";

    // Track both eyes for enrollment auto-stop
    static bool hasLeft = false;
    static bool hasRight = false;

    static void Main(string[] args)
    {
        // 1. Determine Mode
        if (args.Length >= 1 && args[0].ToLower() == "enroll")
        {
            if (args.Length < 2) { Console.WriteLine("Usage: IcamBridge.exe enroll <name>"); return; }
            mode = "enroll";
            saveDir = Path.Combine(ENROLLMENT_DIR, args[1]);
            Console.WriteLine($"=== STARTING ENROLLMENT: {args[1]} ===");
        }
        else
        {
            mode = "recognize";
            saveDir = RECOGNITION_DIR;
            Console.WriteLine("=== STARTING RECOGNITION MODE ===");
        }

        // 2. Setup Directories
        Directory.CreateDirectory(saveDir);
        if (mode == "recognize") Directory.CreateDirectory(ICAM_FRAMES_DIR);

        // 3. Initialize Camera Events
        cam.OnGetIrisImage += OnIrisImage;
        cam.OnGetStatus += OnStatus; // Restored standard SDK event name

        string serial;
        if (cam.Open(out serial) != 0)
        {
            Console.WriteLine("[ERROR] Failed to open iCAM TD100. Check USB connection.");
            return;
        }

        Console.WriteLine($"[CONNECTED] Serial: {serial}");
        cam.SetLive(1);
        cam.StartCapture(4);

        // Handle Manual Exit
        Console.CancelKeyPress += (s, e) => { e.Cancel = true; running = false; };

        // 4. Main Loop
        while (running)
        {
            Thread.Sleep(500);
            // Re-trigger capture in recognize mode if still running
            if (running && mode == "recognize") cam.StartCapture(4);
        }

        Console.WriteLine("[SHUTDOWN] Closing camera...");
        cam.Close();
    }

    static void OnIrisImage(object rightRaw, object leftRaw)
    {
        try
        {
            frameCount++;
            byte[] right = rightRaw as byte[];
            byte[] left = leftRaw as byte[];
            bool savedAny = false;

            // Process Right Eye
            if (right != null && right.Length == WIDTH * HEIGHT)
            {
                string fileName = mode == "enroll" ? "R_Master.png" : $"R_frame_{frameCount:D4}.png";
                SavePng(right, Path.Combine(saveDir, fileName));
                Console.WriteLine($"[SUCCESS] Saved Right Eye: {fileName}");

                hasRight = true;
                savedAny = true;

                if (mode == "recognize") WriteBin(right, OUTPUT_BIN_RIGHT);
            }

            // Process Left Eye
            if (left != null && left.Length == WIDTH * HEIGHT)
            {
                string fileName = mode == "enroll" ? "L_Master.png" : $"L_frame_{frameCount:D4}.png";
                SavePng(left, Path.Combine(saveDir, fileName));
                Console.WriteLine($"[SUCCESS] Saved Left Eye: {fileName}");

                hasLeft = true;
                savedAny = true;

                if (mode == "recognize") WriteBin(left, OUTPUT_BIN_LEFT);
            }

            // Signal to prep_recognition.py or icam.py
            if (savedAny && mode == "recognize")
                File.WriteAllText(READY_FILE, DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString());

            // AUTO-STOP: Enrollment only
            if (mode == "enroll" && hasLeft && hasRight)
            {
                Console.WriteLine("[FINISH] Both eyes captured. Exiting...");
                running = false;
                cam.SetLive(0);
                // Force exit to ensure hardware releases immediately
                Environment.Exit(0);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("[RUNTIME ERROR] " + ex.Message);
        }
    }

    static void WriteBin(byte[] raw, string outputPath)
    {
        try
        {
            string tmp = outputPath + ".tmp";
            File.WriteAllBytes(tmp, raw);
            File.Copy(tmp, outputPath, overwrite: true);
            File.Delete(tmp);
        }
        catch { /* Ignore bin lock issues */ }
    }

    static void SavePng(byte[] grayBytes, string path)
    {
        using (Bitmap bmp = new Bitmap(WIDTH, HEIGHT, PixelFormat.Format8bppIndexed))
        {
            ColorPalette palette = bmp.Palette;
            for (int i = 0; i < 256; i++) palette.Entries[i] = Color.FromArgb(i, i, i);
            bmp.Palette = palette;

            BitmapData bmpData = bmp.LockBits(new Rectangle(0, 0, WIDTH, HEIGHT), ImageLockMode.WriteOnly, PixelFormat.Format8bppIndexed);
            System.Runtime.InteropServices.Marshal.Copy(grayBytes, 0, bmpData.Scan0, grayBytes.Length);
            bmp.UnlockBits(bmpData);
            bmp.Save(path, ImageFormat.Png);
        }
    }

    static void OnStatus(int status, int param)
    {
        // Status 1 or 4 typically indicate a completion or cancellation
        if (status == 1 || status == 4) running = false;
    }
}