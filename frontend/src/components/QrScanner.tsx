import { useEffect, useRef, useState } from "react";
import jsQR from "jsqr";
import { Camera, CameraOff } from "lucide-react";

import { Button } from "@/components/ui/button";

interface QrScannerProps {
  onScan: (data: string) => void;
}

export function QrScanner({ onScan }: QrScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const frameRef = useRef<number>();
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setIsActive(true);
      tick();
    } catch {
      setError("Could not access the camera. You can enter the code manually instead.");
    }
  }

  function stop() {
    if (frameRef.current) cancelAnimationFrame(frameRef.current);
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setIsActive(false);
  }

  function tick() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState !== video.HAVE_ENOUGH_DATA) {
      frameRef.current = requestAnimationFrame(tick);
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, imageData.width, imageData.height);

    if (code?.data) {
      stop();
      onScan(code.data);
      return;
    }

    frameRef.current = requestAnimationFrame(tick);
  }

  useEffect(() => {
    return () => stop();
  }, []);

  return (
    <div className="space-y-3">
      <div className="relative overflow-hidden rounded-xl border border-border bg-secondary" style={{ aspectRatio: "4/3" }}>
        <video ref={videoRef} className={`h-full w-full object-cover ${isActive ? "" : "hidden"}`} muted playsInline />
        {!isActive && (
          <div className="flex h-full w-full items-center justify-center text-muted-foreground">
            <Camera className="h-10 w-10" />
          </div>
        )}
      </div>
      <canvas ref={canvasRef} className="hidden" />

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Button type="button" variant={isActive ? "outline" : "default"} onClick={isActive ? stop : start} className="w-full">
        {isActive ? (
          <>
            <CameraOff className="mr-2 h-4 w-4" />
            Stop camera
          </>
        ) : (
          <>
            <Camera className="mr-2 h-4 w-4" />
            Scan with camera
          </>
        )}
      </Button>
    </div>
  );
}
