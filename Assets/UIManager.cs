using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class UIManager : MonoBehaviour
{
    public GameObject mainPanel;
    public GameObject obtainingDataPanel;
    void Start()
    {
        mainPanel.SetActive(true);
        obtainingDataPanel.SetActive(false);
    }

    public void OpenObtainingData()
    {
        mainPanel.SetActive(false);
        obtainingDataPanel.SetActive(true);
    }
    public void BackToMain()
    {
        mainPanel.SetActive(true);
        obtainingDataPanel.SetActive(false);
    }

    public void CloseAll()
    {
        mainPanel.SetActive(false);
        obtainingDataPanel.SetActive(false);
    }
    // Update is called once per frame
    void Update()
    {
        
    }
}
