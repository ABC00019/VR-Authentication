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

[System.Serializable]
public class UserExistsResponse
{
    public bool exists;
    public string username;
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
    public GameObject loginOptionsPanel;

    [Header("Obtaining Data UI")]
    public Slider progressBar;
    public GameObject continueButton;
    public float progressDuration = 3f;

    [Header("Enrollment")]
    public TMPro.TMP_InputField usernameInputField;

    [Header("References")]
    public Transform userListContent;
    public GameObject userListItemPrefab;

    [Header("Shared Pattern Circles")]
    public GameObject sharedCircles;

    private string baseUrl = "http://127.0.0.1:5000/api";
    private TouchScreenKeyboard vrKeyboard;

    private string selectedUsername = null;

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
        GazePatternRecorder.Instance.OnPatternComplete -= StartAuthentication;
        string username = usernameInputField.text.Trim();
        List<int> pattern = GazePatternRecorder.Instance.GetRecordedPattern();

        if (UserDataManager.Instance.AuthenticateUser(username, pattern))
        {
            Debug.Log("Pattern authentication successful");
            ShowSuccess();
        }
        else
        {
            Debug.Log("Pattern authentication failed");
            ShowAuthFailure();
        }
    }

    // Called by the Sign-In button on the Main panel
    public void SignIn()
    {
        Debug.Log("SignIn button clicked");
        if (GazePatternRecorder.Instance != null)
                GazePatternRecorder.Instance.StopRecording();

        string username = usernameInputField.text.Trim();
        if (string.IsNullOrEmpty(username))
        {
            Debug.Log("Username empty");
            return;
        }

        if (!UserDataManager.Instance.UsernameExists(username))
        {
            Debug.Log($"User '{username}' not enrolled");
            ShowAuthFailure();
            return;
        }

        ShowOnly(loginOptionsPanel);
    }

    private IEnumerator VerifyUserAndSignIn(string username)
    {
        bool irisExists = false;
        yield return CheckIrisExists(username, result => irisExists = result);

        bool patternExists = UserDataManager.Instance.UsernameExists(username);

        if (!irisExists && !patternExists)
        {
            Debug.Log($"User '{username}' not enrolled in either system");
            ShowAuthFailure();
            yield break;
        }

        if (!irisExists || !patternExists)
        {
            Debug.LogWarning($"User '{username}' has incomplete enrollment (iris: {irisExists}, pattern: {patternExists})");
            ShowAuthFailure();
            yield break;
        }

        Debug.Log($"User '{username}' fully enrolled, routing to LoginOptions");
        ShowOnly(loginOptionsPanel);
    }

    // Called by the Iris button on LoginOptions
    public void LoginWithIris()
    {
        ShowOnly(obtainingDataPanel);
        StartCoroutine(ExecuteIrisProcess($"{baseUrl}/authenticate", true));
    }

    // Called by the Pattern button on LoginOptions
    public void LoginWithPattern()
    {
        GazePatternRecorder.Instance.OnPatternComplete = null;
        ShowOnly(backUpPanel);
        GazePatternRecorder.Instance.StartRecording();
        GazePatternRecorder.Instance.OnPatternComplete += StartAuthentication;
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

    // --- Core Communication Logic ---

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
                        ShowBackUpCreation();
                        GazePatternRecorder.Instance.StartRecording();
                        GazePatternRecorder.Instance.OnPatternComplete += FinishEnrollment;
                    }
                    else
                    {
                        // Verify iris identity matches the entered username
                        string enteredUsername = usernameInputField.text.Trim();
                        if (res.identity == enteredUsername)
                        {
                            ShowSuccess();
                        }
                        else
                        {
                            Debug.Log($"Iris matched '{res.identity}' but user entered '{enteredUsername}'");
                            ShowAuthFailure();
                        }
                    }
                }
            }
            else
            {
                Debug.LogError("Server Error: " + webRequest.error);
                if (isAuthenticating) ShowAuthFailure(); else ShowEnrollFailure();
            }
        }
    }

    private IEnumerator CheckIrisExists(string username, System.Action<bool> callback)
    {
        using (UnityWebRequest req = UnityWebRequest.Get($"{baseUrl}/user_exists/{username}"))
        {
            yield return req.SendWebRequest();

            if (req.result == UnityWebRequest.Result.Success)
            {
                UserExistsResponse res = JsonUtility.FromJson<UserExistsResponse>(req.downloadHandler.text);
                callback(res.exists);
            }
            else
            {
                Debug.LogError($"User exists check failed: {req.error}");
                callback(false);
            }
        }
    }

    private void FinishEnrollment()
    {
        GazePatternRecorder.Instance.OnPatternComplete -= FinishEnrollment;
        string username = usernameInputField.text.Trim();
        List<int> pattern = GazePatternRecorder.Instance.GetRecordedPattern();

        // Require a non-empty pattern
        if (pattern.Count < 4)
        {
            Debug.Log("Pattern too short, rolling back enrollment");
            StartCoroutine(RollbackIrisEnrollment(username));
            return;
        }

        UserDataManager.Instance.EnrollUser(username, pattern);
        Debug.Log($"Enrollment complete for '{username}' — both iris and pattern saved");
        ShowSuccess();
    }

    private IEnumerator RollbackIrisEnrollment(string username)
    {
        using (UnityWebRequest req = UnityWebRequest.Delete($"{baseUrl}/delete_user/{username}"))
        {
            yield return req.SendWebRequest();
            if (req.result == UnityWebRequest.Result.Success)
                Debug.Log($"Rolled back iris data for '{username}'");
            else
                Debug.LogError($"Rollback failed: {req.error}");
        }
        ShowEnrollFailure();
    }

    private IEnumerator VerifyAndSaveEnrollment(string username, List<int> pattern)
    {
        bool irisExists = false;
        yield return CheckIrisExists(username, result => irisExists = result);

        if (!irisExists)
        {
            Debug.LogError("Iris data missing for user, rolling back enrollment");
            ShowEnrollFailure();
            yield break;
        }

        UserDataManager.Instance.EnrollUser(username, pattern);
        Debug.Log($"Enrollment complete for '{username}' — iris and pattern both saved");
        ShowSuccess();
    }


    public void DeleteSelectedUser()
    {
        if (string.IsNullOrEmpty(selectedUsername))
        {
            Debug.Log("No user selected");
            return;
        }

        DeleteUser(selectedUsername);
        ShowUserListPanel();  // refresh the list after deletion
    }
    
    public void DeleteUser(string username)
    {
        StartCoroutine(DeleteUserCoroutine(username));
    }

    private IEnumerator DeleteUserCoroutine(string username)
    {
        // Delete iris data on server
        using (UnityWebRequest req = UnityWebRequest.Delete($"{baseUrl}/delete_user/{username}"))
        {
            yield return req.SendWebRequest();
            if (req.result != UnityWebRequest.Result.Success)
                Debug.LogWarning($"Iris delete failed: {req.error}");
        }

        // Delete pattern data locally
        UserDataManager.Instance.DeleteUser(username);
        Debug.Log($"User '{username}' deleted from both systems");
    }

    // --- UI Navigation Methods ---

    public void ShowSuccess() { ShowOnly(successPanel); }
    public void ShowAuthFailure() { ShowOnly(authFailurePanel); }
    public void ShowEnrollFailure() { ShowOnly(enrollFailurePanel); }
    public void ShowBackUpCreation() { ShowOnly(backUpCreationPanel); }
    public void ShowBackUp() { ShowOnly(backUpPanel); }

    public void BackToMain() 
    { 
        if (GazePatternRecorder.Instance != null)
        GazePatternRecorder.Instance.StopRecording();
        ShowOnly(mainPanel); 
    }

    public void ShowLoginOptions() { ShowOnly(loginOptionsPanel); }

    private void ShowOnly(GameObject target)
    {
        GameObject[] allPanels = {
            mainPanel, obtainingDataPanel, successPanel,
            authFailurePanel, enrollFailurePanel,
            backUpCreationPanel, backUpPanel, userListPanel,
            loginOptionsPanel, sharedCircles
        };

        foreach (GameObject panel in allPanels)
        {
            if (panel != null)
                panel.SetActive(panel == target);
        }

        if (sharedCircles != null)
            sharedCircles.SetActive(target == backUpCreationPanel || target == backUpPanel);
    }

    public void ShowUserListPanel()
    {
        selectedUsername = null;  // clear any previous selection

        foreach (Transform child in userListContent)
            Destroy(child.gameObject);

        foreach (UserProfile user in UserDataManager.Instance.GetAllUsers())
        {
            GameObject item = Instantiate(userListItemPrefab, userListContent);
            item.GetComponentInChildren<TMPro.TextMeshProUGUI>().text = user.username;

            // Wire the item's button to select this user
            Button btn = item.GetComponent<Button>();
            if (btn != null)
            {
                string captured = user.username;
                btn.onClick.AddListener(() => SelectUser(captured));
            }
        }
        ShowOnly(userListPanel);
    }

    public void SelectUser(string username)
    {
        selectedUsername = username;
        Debug.Log($"Selected user: {username}");
        // Optional: visually highlight the selected item in the list
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