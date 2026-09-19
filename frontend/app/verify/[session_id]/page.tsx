"use client";
/**
 * ArgusCX -- Mobile Verification Capture Page
 * Renders the live challenge-response camera capture UI.
 * iOS Safari compatible: video element with playsinline + muted + autoplay.
 */
import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "next/navigation";

interface Challenge {
  step_index: number;
  challenge_type: string;
  instruction_text: string;
  required_action: string;
}

interface SessionData {
  session_id: string;
  challenges: Challenge[];
  capture_url: string;
  expires_at: string;
}

type CapturePhase =
  | "loading"
  | "permission_request"
  | "permission_denied"
  | "challenge"
  | "uploading"
  | "completed"
  | "error"
  | "expired";

export default function VerifyPage() {
  const params = useParams<{ session_id: string }>();
  const sessionId = params.session_id;
  const [sessionToken] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return new URLSearchParams(window.location.search).get("token");
  });
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [phase, setPhase] = useState<CapturePhase>("loading");
  const [session, setSession] = useState<SessionData | null>(null);
  const [currentChallengeIdx, setCurrentChallengeIdx] = useState(0);
  const [completedChallenges, setCompletedChallenges] = useState<number[]>([]);
  const [error, setError] = useState<string>("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [qualityWarning, setQualityWarning] = useState<string>("");
  const [capturedFrames, setCapturedFrames] = useState<{ blob: Blob; challengeIdx: number }[]>([]);

  // Re-attach the stream once the <video> element is actually in the DOM.
  // requestCamera() may call setPhase("challenge") before the video element
  // is mounted, making videoRef.current null at that point.
  useEffect(() => {
    if (phase === "challenge" && videoRef.current && streamRef.current) {
      if (videoRef.current.srcObject !== streamRef.current) {
        videoRef.current.srcObject = streamRef.current;
        videoRef.current.play().catch(() => {/* autoplay policy — muted so this rarely fails */});
      }
    }
  }, [phase]);

  // Fetch the capture plan using the scoped token embedded in the QR/link.
  useEffect(() => {
    if (!sessionId || !sessionToken) {
      setError("This verification link is incomplete. Request a new link from support.");
      setPhase("error");
      return;
    }

    fetch(`/api/v1/sessions/${encodeURIComponent(sessionId)}`, {
      headers: { "X-Session-Token": sessionToken },
    })
      .then((response) => {
        if (response.status === 410) {
          setPhase("expired");
          return null;
        }
        if (!response.ok) throw new Error("Session not found or this link has expired.");
        return response.json() as Promise<SessionData>;
      })
      .then((data) => {
        if (!data) return;
        setSession(data);
        setPhase("permission_request");
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Could not load this verification session.");
        setPhase("error");
      });
  }, [sessionId, sessionToken]);

  const requestCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setPhase("challenge");
    } catch (err: any) {
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setPhase("permission_denied");
      } else {
        setError(`Camera error: ${err.message}`);
        setPhase("error");
      }
    }
  }, []);

  const captureFrame = async (): Promise<Blob | null> => {
    if (!videoRef.current) return null;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    
    return new Promise((resolve) => {
      canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.9);
    });
  };

  const completeChallenge = useCallback(async () => {
    const idx = currentChallengeIdx;
    
    const blob = await captureFrame();
    const newFrames = blob ? [...capturedFrames, { blob, challengeIdx: idx }] : capturedFrames;
    if (blob) {
      setCapturedFrames(newFrames);
    }

    const nextCompleted = [...completedChallenges, idx];
    setCompletedChallenges(nextCompleted);
    const challenges = session?.challenges || [];
    if (idx + 1 >= challenges.length) {
      // All challenges done -- submit
      submitSession(nextCompleted, newFrames);
    } else {
      setCurrentChallengeIdx(idx + 1);
    }
  }, [completedChallenges, currentChallengeIdx, session, capturedFrames]);

  const submitSession = useCallback(async (challengeIndexes: number[], framesToUpload: { blob: Blob; challengeIdx: number }[]) => {
    if (!sessionToken) {
      setError("This verification link is incomplete. Request a new link from support.");
      setPhase("error");
      return;
    }
    setPhase("uploading");
    setUploadProgress(10);
    try {
      const evidenceIds: string[] = [];
      const evidenceUrls: string[] = [];

      for (let i = 0; i < framesToUpload.length; i++) {
        const { blob, challengeIdx } = framesToUpload[i];
        setUploadProgress(10 + (i / framesToUpload.length) * 40); // 10% to 50%
        const formData = new FormData();
        formData.append("file", blob, `frame_${challengeIdx}_${Date.now()}.jpg`);
        
        try {
          const uploadRes = await fetch("/api/v1/evidence/upload", {
            method: "POST",
            body: formData,
          });
          if (uploadRes.ok) {
            const result = await uploadRes.json();
            evidenceIds.push(result.id);
            evidenceUrls.push(result.url);
          } else {
            evidenceIds.push(`frame_${challengeIdx}_${Date.now()}`);
          }
        } catch (e) {
          evidenceIds.push(`frame_${challengeIdx}_${Date.now()}`);
        }
      }

      setUploadProgress(60);
      const resp = await fetch(`/api/v1/sessions/${encodeURIComponent(sessionId)}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Session-Token": sessionToken },
        body: JSON.stringify({
          assurance_level: "live_video",
          evidence_ids: evidenceIds.length > 0 ? evidenceIds : challengeIndexes.map((i) => `frame_${i}_${Date.now()}`),
          evidence_urls: evidenceUrls,
        }),
      });
      setUploadProgress(100);
      if (resp.ok) {
        setPhase("completed");
      } else {
        throw new Error("Submission failed");
      }
    } catch (e: any) {
      setError(e.message);
      setPhase("error");
    } finally {
      // Stop camera
      streamRef.current?.getTracks().forEach((t) => t.stop());
    }
  }, [sessionId, sessionToken]);

  const challenges = session?.challenges || [];
  const currentChallenge = challenges[currentChallengeIdx];
  const progressPct = challenges.length ? (completedChallenges.length / challenges.length) * 100 : 0;

  // ── RENDER ──
  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.logo}>ArgusCX</div>
        <div style={styles.headerSub}>Return Verification</div>
      </div>

      {/* Progress bar */}
      {phase === "challenge" && challenges.length > 0 && (
        <div style={styles.progressBar}>
          <div style={{ ...styles.progressFill, width: `${progressPct}%` }} />
        </div>
      )}

      {/* Main content */}
      <div style={styles.content}>
        {phase === "loading" && (
          <div style={styles.centered}>
            <div style={styles.spinner} />
            <p style={styles.subText}>Loading session...</p>
          </div>
        )}

        {phase === "permission_request" && (
          <div style={styles.centered}>
            <div style={styles.iconLarge}>📷</div>
            <h1 style={styles.title}>Camera Access Needed</h1>
            <p style={styles.bodyText}>
              We need your camera to capture live evidence of the product.
              Your session is secure and expires in 30 minutes.
            </p>
            <button style={styles.primaryBtn} onClick={requestCamera}>
              Allow Camera
            </button>
            <p style={styles.hint}>
              iOS: tap Allow when prompted. Android: tap Allow or OK.
            </p>
          </div>
        )}

        {phase === "permission_denied" && (
          <div style={styles.centered}>
            <div style={styles.iconLarge}>🔒</div>
            <h1 style={styles.title}>Camera Access Denied</h1>
            <p style={styles.bodyText}>
              Please enable camera access in your browser settings and refresh this page.
            </p>
            <p style={styles.hint}>
              iOS: Settings → Safari → Camera → Allow<br />
              Android: Site settings → Camera → Allow
            </p>
            <button style={styles.secondaryBtn} onClick={() => window.location.reload()}>
              Try Again
            </button>
          </div>
        )}

        {phase === "challenge" && (
          <div style={styles.challengeContainer}>
            {/* Live camera feed */}
            <div style={styles.videoWrapper}>
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                style={styles.video}
              />
              {/* Challenge overlay */}
              <div style={styles.videoOverlay}>
                <div style={styles.challengeStep}>
                  Step {currentChallengeIdx + 1} of {challenges.length}
                </div>
              </div>
            </div>

            {/* Challenge instruction */}
            {currentChallenge && (
              <div style={styles.challengeCard}>
                <div style={styles.challengeIcon}>
                  {getChallengeIcon(currentChallenge.challenge_type)}
                </div>
                <p style={styles.challengeInstruction}>
                  {currentChallenge.instruction_text}
                </p>
                {qualityWarning && (
                  <div style={styles.qualityWarning}>{qualityWarning}</div>
                )}
                <button style={styles.primaryBtn} onClick={completeChallenge}>
                  Done ✓
                </button>
              </div>
            )}
          </div>
        )}

        {phase === "uploading" && (
          <div style={styles.centered}>
            <div style={styles.spinner} />
            <h1 style={styles.title}>Submitting Evidence</h1>
            <div style={styles.uploadBar}>
              <div style={{ ...styles.uploadFill, width: `${uploadProgress}%` }} />
            </div>
            <p style={styles.subText}>{uploadProgress}% — Please keep this page open</p>
          </div>
        )}

        {phase === "completed" && (
          <div style={styles.centered}>
            <div style={styles.iconLarge}>✅</div>
            <h1 style={styles.title}>Verification Complete</h1>
            <p style={styles.bodyText}>
              Your evidence has been submitted for review.
              You will be notified of the outcome shortly.
            </p>
            <p style={styles.hint}>You may now close this window.</p>
          </div>
        )}

        {phase === "expired" && (
          <div style={styles.centered}>
            <div style={styles.iconLarge}>⏰</div>
            <h1 style={styles.title}>Session Expired</h1>
            <p style={styles.bodyText}>
              This verification link has expired. Please contact support
              to receive a new verification link.
            </p>
          </div>
        )}

        {phase === "error" && (
          <div style={styles.centered}>
            <div style={styles.iconLarge}>⚠️</div>
            <h1 style={styles.title}>Something Went Wrong</h1>
            <p style={styles.bodyText}>{error || "An unexpected error occurred."}</p>
            <button style={styles.secondaryBtn} onClick={() => window.location.reload()}>
              Retry
            </button>
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={styles.footer}>
        <p style={styles.footerText}>Secured by ArgusCX · Evidence encrypted in transit</p>
      </div>
    </div>
  );
}

function getChallengeIcon(type: string): string {
  const icons: Record<string, string> = {
    SHOW_FRONT: "📱", SHOW_BACK: "🔄", MOVE_LEFT: "⬅️",
    MOVE_RIGHT: "➡️", MOVE_UP: "⬆️", FOCUS_SERIAL: "🔍",
    SHOW_PACKAGING: "📦", SHOW_DAMAGE: "🔎", ROTATE_PRODUCT: "🔃",
  };
  return icons[type] || "📸";
}

const styles: Record<string, React.CSSProperties> = {
  container:           { minHeight: "100vh", background: "var(--bg-primary)", color: "var(--text-primary)", fontFamily: "var(--font-sans)", display: "flex", flexDirection: "column" },
  header:              { background: "var(--bg-elevated)", padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border)" },
  logo:                { fontSize: "18px", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.02em" },
  headerSub:           { fontSize: "12px", color: "var(--text-muted)", fontWeight: 500 },
  progressBar:         { height: "3px", background: "var(--border)" },
  progressFill:        { height: "100%", background: "var(--accent)", transition: "width 0.4s ease" },
  content:             { flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", padding: "24px 20px", maxWidth: 430, margin: "0 auto", width: "100%" },
  centered:            { display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", gap: "16px" },
  iconLarge:           { fontSize: "48px" },
  title:               { fontSize: "20px", fontWeight: 600, margin: 0, color: "var(--text-primary)" },
  bodyText:            { fontSize: "15px", color: "var(--text-secondary)", lineHeight: 1.6, margin: 0 },
  hint:                { fontSize: "13px", color: "var(--text-muted)", lineHeight: 1.5 },
  subText:             { fontSize: "14px", color: "var(--text-secondary)" },
  primaryBtn:          { background: "var(--text-primary)", color: "var(--bg-primary)", border: "none", borderRadius: "8px", padding: "16px 32px", fontSize: "16px", fontWeight: 600, cursor: "pointer", width: "100%" },
  secondaryBtn:        { background: "var(--bg-elevated)", color: "var(--text-primary)", border: "1px solid var(--border-strong)", borderRadius: "8px", padding: "14px 28px", fontSize: "15px", fontWeight: 500, cursor: "pointer" },
  spinner:             { width: "40px", height: "40px", border: "3px solid var(--border)", borderTop: "3px solid var(--text-primary)", borderRadius: "50%", animation: "spin 1s linear infinite" },
  uploadBar:           { width: "100%", height: "6px", background: "var(--bg-elevated)", borderRadius: "3px", overflow: "hidden" },
  uploadFill:          { height: "100%", background: "var(--accent)", transition: "width 0.3s ease" },
  challengeContainer:  { display: "flex", flexDirection: "column", gap: "16px", width: "100%" },
  videoWrapper:        { position: "relative", borderRadius: "12px", overflow: "hidden", background: "var(--bg-elevated)", aspectRatio: "3/4", maxHeight: "65vh" },
  video:               { width: "100%", height: "100%", objectFit: "cover" },
  videoOverlay:        { position: "absolute", top: "12px", left: "12px", right: "12px" },
  challengeStep:       { background: "var(--bg-surface)", border: "1px solid var(--border)", color: "var(--text-primary)", padding: "4px 10px", borderRadius: "12px", fontSize: "12px", fontWeight: 500, display: "inline-block" },
  challengeCard:       { background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: "12px", padding: "20px", display: "flex", flexDirection: "column", alignItems: "center", gap: "12px", textAlign: "center" },
  challengeIcon:       { fontSize: "32px" },
  challengeInstruction:{ fontSize: "16px", color: "var(--text-primary)", fontWeight: 500, lineHeight: 1.4, margin: 0 },
  qualityWarning:      { background: "rgba(243,184,91,0.1)", border: "1px solid var(--warning)", borderRadius: "6px", padding: "8px 12px", fontSize: "13px", color: "var(--warning)" },
  footer:              { padding: "16px", textAlign: "center" },
  footerText:          { fontSize: "11px", color: "var(--text-muted)", margin: 0 },
};
