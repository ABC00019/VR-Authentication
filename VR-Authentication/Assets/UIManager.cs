using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;

[System.Serializable]
public class AuthResponse
{
    public string status;
    public string identity;
    public string message;
}

public class UIManager : MonoBehaviour
{
    [Header("Panels")]
    public GameObject mainPanel;
    public GameObject obtainingDataPanel;
    public GameObject successPanel;
    public GameObject authFailurePanel;
    public GameObject enrollFailurePanel;
    public GameObject backUpCreationPanel;
    public GameObject backUpPanel;
    public GameObject keyboardPanel;
    public GameObject userListPanel;

    [Header("Obtaining Data UI")]
    public Slider progressBar;
    public GameObject continueButton;
    public float progressDuration = 3f;

    [Header("Enrollment")]
    public TMPro.TMP_InputField usernameInputField;

    [Header("References")]
    public Transform userListContent;
    public GameObject userListItemPrefab;

    private string baseUrl = "http://127.0.0.1:5000/api";
    private TouchScreenKeyboard vrKeyboard;

    void Start() { ShowOnly(mainPanel); }

    void Update()
    {
        // Update the input field text as the user types on the VR system keyboard
        if (vrKeyboard != null && vrKeyboard.active)
        {
            usernameInputField.text = vrKeyboard.text;
        }
    }

    // --- Button Triggers ---

    public void StartAuthentication()
    {
        ShowOnly(obtainingDataPanel);
        StartCoroutine(ExecuteIrisProcess($"{baseUrl}/authenticate", true));
    }

    public void StartEnrollment()
    {
        string username = usernameInputField.text.Trim();
        if (string.IsNullOrEmpty(username)) return;

        ShowOnly(obtainingDataPanel);
        StartCoroutine(ExecuteIrisProcess($"{baseUrl}/enroll/{username}", false));
    }

    public void OpenSystemKeyboard()
    {
        vrKeyboard = TouchScreenKeyboard.Open(usernameInputField.text, TouchScreenKeyboardType.Default, false, false, false, false, "Enter Username");
    }

    // --- Core Communication Logic (Only ONE copy) ---

    private IEnumerator ExecuteIrisProcess(string url, bool isAuthenticating)
    {
        StartCoroutine(RunProgressBar());

        using (UnityWebRequest webRequest = UnityWebRequest.Get(url))
        {
            yield return webRequest.SendWebRequest();

            if (webRequest.result == UnityWebRequest.Result.Success)
            {
                AuthResponse res = JsonUtility.FromJson<AuthResponse>(webRequest.downloadHandler.text);

                if (res.status == "success")
                {
                    if (!isAuthenticating)
                    {
                        // Proceed to Gaze Backup after Iris scan for Enrollment
                        ShowBackUpCreation();
                        GazePatternRecorder.Instance.StartRecording();
                        GazePatternRecorder.Instance.OnPatternComplete += FinishEnrollment;
                    }
                    else
                    {
                        ShowSuccess();
                    }
                }
                else
                {
                    if (isAuthenticating) ShowAuthFailure(); else ShowEnrollFailure();
                }
            }
            else
            {
                Debug.LogError("Server Error: " + webRequest.error);
                if (isAuthenticating) ShowAuthFailure(); else ShowEnrollFailure();
            }
        }
    }

    private void FinishEnrollment()
    {
        GazePatternRecorder.Instance.OnPatternComplete -= FinishEnrollment;
        string username = usernameInputField.text.Trim();
        List<int> pattern = GazePatternRecorder.Instance.GetRecordedPattern();
        UserDataManager.Instance.EnrollUser(username, pattern);
        ShowSuccess();
    }

    // --- UI Navigation Methods ---

    public void ShowSuccess() { ShowOnly(successPanel); }
    public void ShowAuthFailure() { ShowOnly(authFailurePanel); }
    public void ShowEnrollFailure() { ShowOnly(enrollFailurePanel); }
    public void ShowBackUpCreation() { ShowOnly(backUpCreationPanel); }
    public void ShowBackUp() { ShowOnly(backUpPanel); }
    public void BackToMain() { ShowOnly(mainPanel); }

    private void ShowOnly(GameObject target)
    {
        GameObject[] allPanels = {
            mainPanel, obtainingDataPanel, successPanel,
            authFailurePanel, enrollFailurePanel,
            backUpCreationPanel, backUpPanel, userListPanel,
            keyboardPanel
        };

        foreach (GameObject panel in allPanels)
        {
            if (panel != null)
                panel.SetActive(panel == target);
        }
    }

    private IEnumerator RunProgressBar()
    {
        progressBar.value = 0f;
        float elapsed = 0f;
        continueButton.SetActive(false);

        while (elapsed < progressDuration)
        {
            elapsed += Time.deltaTime;
            progressBar.value = Mathf.Clamp01(elapsed / progressDuration);
            yield return null;
        }
        progressBar.value = 1f;
    }
}