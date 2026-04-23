using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TS.GazeInteraction;

public class GazePatternRecorder : MonoBehaviour
{
    public static GazePatternRecorder Instance;

    [Header("References")]
    public Transform[] circles;
    public GazeInteractable[] circleInteractables;

    [Header("Visual Feedback")]
    public Color defaultColor = Color.white;
    public Color selectedColor = Color.green;
    public Color dwellColor = Color.yellow;

    private List<int> recordedPattern = new List<int>();
    private bool isRecording = false;

    public System.Action<int> OnCircleRegistered;
    public System.Action OnPatternComplete;

    void Awake()
    {
        if (Instance != null && Instance != this) { Destroy(gameObject); return; }
        Instance = this;
    }

    public void StartRecording()
    {
        Debug.Log("StartRecording called");
        recordedPattern.Clear();
        isRecording = true;

        // Reset all circle colors
        for (int i = 0; i < circles.Length; i++)
            UpdateCircleColor(i, defaultColor);

        // Subscribe to each circle's events
        for (int i = 0; i < circleInteractables.Length; i++)
        {
            int captured = i;
            circleInteractables[i].OnGazeEnter.AddListener(() => OnCircleEnter(captured));
            circleInteractables[i].OnGazeActivated.AddListener(() => OnCircleActivated(captured));
            circleInteractables[i].OnGazeExit.AddListener(() => OnCircleExit(captured));
        }
    }

    public void StopRecording()
    {
        isRecording = false;

        // Unsubscribe from all events
        for (int i = 0; i < circleInteractables.Length; i++)
        {
            circleInteractables[i].OnGazeEnter.RemoveAllListeners();
            circleInteractables[i].OnGazeActivated.RemoveAllListeners();
            circleInteractables[i].OnGazeExit.RemoveAllListeners();
        }

        // Reset all circle colors to default
        for (int i = 0; i < circles.Length; i++)
            UpdateCircleColor(i, defaultColor);
    }

    private void OnCircleEnter(int index)
    {
        if (!isRecording) return;
        if (recordedPattern.Contains(index)) return;
        UpdateCircleColor(index, dwellColor);
    }

    private void OnCircleActivated(int index)
    {
        if (!isRecording) return;
        if (recordedPattern.Contains(index)) return;

        recordedPattern.Add(index);
        UpdateCircleColor(index, selectedColor);
        OnCircleRegistered?.Invoke(index);
        Debug.Log($"Circle {index} registered. Pattern so far: {string.Join(",", recordedPattern)}");
    }

    private void OnCircleExit(int index)
    {
        if (!isRecording) return;
        if (recordedPattern.Contains(index)) return;
        UpdateCircleColor(index, defaultColor);
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

    private void UpdateCircleColor(int index, Color color)
    {
        RawImage img = circles[index].GetComponent<RawImage>();
        if (img != null)
            img.color = color;
    }
}