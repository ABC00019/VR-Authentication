using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;

public class UserDataManager : MonoBehaviour
{
    public static UserDataManager Instance;

    private UserDatabase database = new UserDatabase();
    private string savePath;

    void Awake()
    {
        // only one UserDataManager can exist
        if (Instance != null && Instance != this) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);

        savePath = Path.Combine(Application.persistentDataPath, "users.json");
        Load();
    }

    public void Save()
    {
        string json = JsonUtility.ToJson(database, prettyPrint: true);
        File.WriteAllText(savePath, json);
    }

    public void Load()
    {
        if (File.Exists(savePath))
        {
            string json = File.ReadAllText(savePath);
            database = JsonUtility.FromJson<UserDatabase>(json);
        }
    }

    public void DeleteUser(string username)
    {
        database.users.RemoveAll(u => u.username == username);
        Save();
    }

    public bool UsernameExists(string username)
    {
        return database.users.Exists(u => u.username == username);
    }

    public void EnrollUser(string username, List<int> pattern)
    {
        // Replace if exists, otherwise add
        database.users.RemoveAll(u => u.username == username);
        database.users.Add(new UserProfile(username, pattern));
        Save();
    }

    public List<UserProfile> GetAllUsers()
    {
        return database.users;
    }

    public bool AuthenticateUser(string username, List<int> attemptedPattern)
    {
        UserProfile profile = database.users.Find(u => u.username == username);
        if (profile == null) return false;
        if (profile.gazePattern.Count != attemptedPattern.Count) return false;

        for (int i = 0; i < profile.gazePattern.Count; i++)
        {
            if (profile.gazePattern[i] != attemptedPattern[i]) return false;
        }
        return true;
    }
}
