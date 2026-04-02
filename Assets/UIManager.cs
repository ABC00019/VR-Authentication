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

    [Header("Obtaining Data UI")]
    public Slider progressBar;
    public GameObject continueButton;
    public float progressDuration = 3f;

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
            backUpCreationPanel, backUpPanel
        };

        foreach (GameObject panel in allPanels)
        {
            if (panel != null)
                panel.SetActive(panel == target);
        }
    }
}