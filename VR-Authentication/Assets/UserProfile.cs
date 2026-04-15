using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[System.Serializable]
public class UserProfile
{
    public string username;
    public List<int> gazePattern; // sequence of circle indices 0-8 (the pattern is basically just a pin in a 3x3 grid)

    public UserProfile(string username, List<int> pattern)
    {
        this.username = username;
        this.gazePattern = pattern;
    }
}

[System.Serializable]
public class UserDatabase
{
    public List<UserProfile> users = new List<UserProfile>();
}
