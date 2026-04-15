using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class VRKeyboard : MonoBehaviour
{
    public static VRKeyboard Instance;

    [Header("References")]
    public Transform keyboardContainer;
    public GameObject keyButtonPrefab;

    private TMP_InputField targetInputField;

    private string[] rows = new string[]
    {
        "QWERTYUIOP",
        "ASDFGHJKL",
        "ZXCVBNM"
    };

    void Awake()
    {
        if (Instance != null && Instance != this) { Destroy(gameObject); return; }
        Instance = this;
        GenerateKeyboard();
        gameObject.SetActive(false);
    }

    private void GenerateKeyboard()
    {
        foreach (string row in rows)
        {
            // Create a row container
            GameObject rowObj = new GameObject("Row_" + row[0]);
            rowObj.transform.SetParent(keyboardContainer, false);

            HorizontalLayoutGroup hlg = rowObj.AddComponent<HorizontalLayoutGroup>();
            hlg.spacing = 5f;
            hlg.childAlignment = TextAnchor.MiddleCenter;
            hlg.childForceExpandWidth = false;
            hlg.childForceExpandHeight = false;

            RectTransform rowRect = rowObj.GetComponent<RectTransform>();
            rowRect.sizeDelta = new Vector2(0, 60);

            // Create a button for each character in the row
            foreach (char c in row)
            {
                GameObject keyObj = Instantiate(keyButtonPrefab, rowObj.transform);
                keyObj.name = "Key_" + c;

                // Set label
                keyObj.GetComponentInChildren<TextMeshProUGUI>().text = c.ToString();

                // Capture character for the lambda
                char captured = c;
                keyObj.GetComponent<Button>().onClick.AddListener(() =>
                    OnKeyPressed(captured.ToString()));
            }
        }

        // Bottom row - Backspace, Space, Done
        GameObject bottomRow = new GameObject("Row_Bottom");
        bottomRow.transform.SetParent(keyboardContainer, false);

        HorizontalLayoutGroup bottomHlg = bottomRow.AddComponent<HorizontalLayoutGroup>();
        bottomHlg.spacing = 5f;
        bottomHlg.childAlignment = TextAnchor.MiddleCenter;
        bottomHlg.childForceExpandWidth = false;
        bottomHlg.childForceExpandHeight = false;

        RectTransform bottomRect = bottomRow.GetComponent<RectTransform>();
        bottomRect.sizeDelta = new Vector2(0, 60);

        AddSpecialKey(bottomRow, "Back", OnBackspace);
        AddSpecialKey(bottomRow, "Space", OnSpace);
        AddSpecialKey(bottomRow, "Done", OnDone);
    }

    private void AddSpecialKey(GameObject row, string label, UnityEngine.Events.UnityAction action)
    {
        GameObject keyObj = Instantiate(keyButtonPrefab, row.transform);
        keyObj.name = "Key_" + label;
        keyObj.GetComponentInChildren<TextMeshProUGUI>().text = label;
        keyObj.GetComponent<Button>().onClick.AddListener(action);
    }

    public void Open(TMP_InputField inputField)
    {
        targetInputField = inputField;
        gameObject.SetActive(true);
    }

    public void Close()
    {
        gameObject.SetActive(false);
        targetInputField = null;
    }

    public void OnKeyPressed(string character)
    {
        if (targetInputField == null) return;
        targetInputField.text += character;
    }

    public void OnBackspace()
    {
        if (targetInputField == null) return;
        if (targetInputField.text.Length > 0)
            targetInputField.text = targetInputField.text
                .Substring(0, targetInputField.text.Length - 1);
    }

    public void OnSpace()
    {
        if (targetInputField == null) return;
        targetInputField.text += " ";
    }

    public void OnDone()
    {
        Close();
    }
}