using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class GazePatternRecorder : MonoBehaviour
{
    public static GazePatternRecorder Instance;

    [Header("References")]
    public EyeTrackingManager eyeTrackingManager;
    public Transform[] circles; // Assign all 9 circle transforms in order in Inspector

    [Header("Settings")]
    public float dwellTime = 1.0f;      // Seconds to look at a circle to register it
    public float circleRadius = 0.05f;  // World-space radius to count as "looking at" circle

    // State
    private List<int> recordedPattern = new List<int>();
    private int currentDwellTarget = -1;
    private float dwellTimer = 0f;
    private bool isRecording = false;

    public System.Action<int> OnCircleRegistered;   // Fires when a circle is added to pattern
    public System.Action OnPatternComplete;          // Fires when user confirms pattern

    void Awake()
    {
        if (Instance != null && Instance != this) { Destroy(gameObject); return; }
        Instance = this;
    }

    void Update()
    {
        if (!isRecording) return;

        // Get current gaze direction in world space
        Vector3 gazeDirection = eyeTrackingManager.gazeOriginTrans.forward;
        Vector3 gazeOrigin = eyeTrackingManager.gazeOriginTrans.position;

        int gazedCircle = GetGazedCircle(gazeOrigin, gazeDirection);

        if (gazedCircle == -1)
        {
            // Not looking at any circle reset dwell
            dwellTimer = 0f;
            currentDwellTarget = -1;
            return;
        }

        // Already recorded this circle - skip
        if (recordedPattern.Contains(gazedCircle)) return;

        if (gazedCircle == currentDwellTarget)
        {
            dwellTimer += Time.deltaTime;
            if (dwellTimer >= dwellTime)
            {
                RegisterCircle(gazedCircle);
                dwellTimer = 0f;
                currentDwellTarget = -1;
            }
        }
        else
        {
            // Switched to a new circle - restart dwell
            currentDwellTarget = gazedCircle;
            dwellTimer = 0f;
        }
    }

    private int GetGazedCircle(Vector3 origin, Vector3 direction)
    {
        for (int i = 0; i < circles.Length; i++)
        {
            // Distance from gaze ray to circle center
            Vector3 toCircle = circles[i].position - origin;
            float dist = Vector3.Cross(direction, toCircle).magnitude;
            if (dist < circleRadius) return i;
        }
        return -1;
    }

    private void RegisterCircle(int index)
    {
        recordedPattern.Add(index);
        OnCircleRegistered?.Invoke(index);
    }

    public void StartRecording()
    {
        recordedPattern.Clear();
        currentDwellTarget = -1;
        dwellTimer = 0f;
        isRecording = true;
    }

    public void StopRecording()
    {
        isRecording = false;
    }

    public void ConfirmPattern()
    {
        StopRecording();
        OnPatternComplete?.Invoke();
    }

    public List<int> GetRecordedPattern()
    {
        return new List<int>(recordedPattern);
    }
}