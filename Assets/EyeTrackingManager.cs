using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using VIVE.OpenXR;
using VIVE.OpenXR.EyeTracker;

public class EyeTrackingManager : MonoBehaviour
{
    public XrSingleEyeGazeDataHTC leftGaze;
    public XrSingleEyeGazeDataHTC rightGaze;

    public Transform originXRRig;
    public Transform gazeOriginTrans; // Your sphere transform

    void Update()
    {
        // Get eye gaze data
        XR_HTC_eye_tracker.Interop.GetEyeGazeData(out XrSingleEyeGazeDataHTC[] gazes);

        leftGaze = gazes[(int)XrEyePositionHTC.XR_EYE_POSITION_LEFT_HTC];
        rightGaze = gazes[(int)XrEyePositionHTC.XR_EYE_POSITION_RIGHT_HTC];

        // Update sphere position and rotation to follow left gaze
        gazeOriginTrans.position = originXRRig.position + leftGaze.gazePose.position.ToUnityVector();
        gazeOriginTrans.rotation = originXRRig.rotation * leftGaze.gazePose.orientation.ToUnityQuaternion();
    }
}
