using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

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

    [Header("Obtaining Data UI")]
    public Slider progressBar;
    public GameObject continueButton;
    public float progressDuration = 3f;

    [Header("User List Panel")]
    public GameObject userListPanel;
    public Transform userListContent;   // scroll view content parent
    public GameObject userListItemPrefab; // prefab with a text component for each user's name

    [Header("Enrollment")]
    public TMPro.TMP_InputField usernameInputField;

    void Start()
    {
        ShowOnly(mainPanel);
    }

    void Update() { }

    // Panel navigation

    public void OpenObtainingData()
    {
        ShowOnly(obtainingDataPanel);
        continueButton.SetActive(false);
        StartCoroutine(RunProgressBar());
    }

    public void BackToMain()
    {
        ShowOnly(mainPanel);
    }

    public void ShowSuccess()
    {
        ShowOnly(successPanel);
    }

    public void ShowAuthFailure()
    {
        ShowOnly(authFailurePanel);
    }

    public void ShowEnrollFailure()
    {
        ShowOnly(enrollFailurePanel);
    }

    public void ShowBackUpCreation()
    {
        ShowOnly(backUpCreationPanel);
    }

    public void ShowBackUp()
    {
        ShowOnly(backUpPanel);
    }

    public void CloseAll()
    {
        ShowOnly(null);
    }

    // Progress Bar
    private IEnumerator RunProgressBar()
    {
        progressBar.value = 0f;
        float elapsed = 0f;

        while (elapsed < progressDuration)
        {
            elapsed += Time.deltaTime;
            progressBar.value = Mathf.Clamp01(elapsed / progressDuration);
            yield return null;
        }

        progressBar.value = 1f;
        continueButton.SetActive(true);
    }

    // Utility
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

    public void ShowUserList()
    {
        // Clear old entries
        foreach (Transform child in userListContent)
            Destroy(child.gameObject);

        // Populate from saved data
        foreach (UserProfile user in UserDataManager.Instance.GetAllUsers())
        {
            GameObject item = Instantiate(userListItemPrefab, userListContent);
            item.GetComponentInChildren<TMPro.TextMeshProUGUI>().text = user.username;
        }
        ShowOnly(userListPanel);
    }

    public void StartEnrollment()
    {
        string username = usernameInputField.text.Trim();
        if (string.IsNullOrEmpty(username)) 
            return;
        ShowOnly(backUpCreationPanel);
        GazePatternRecorder.Instance.StartRecording();
        GazePatternRecorder.Instance.OnPatternComplete += FinishEnrollment;
    }

    private void FinishEnrollment()
    {
        GazePatternRecorder.Instance.OnPatternComplete -= FinishEnrollment;
        string username = usernameInputField.text.Trim();
        List<int> pattern = GazePatternRecorder.Instance.GetRecordedPattern();
        UserDataManager.Instance.EnrollUser(username, pattern);
        ShowSuccess();
    }
}