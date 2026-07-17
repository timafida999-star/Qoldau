import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { CheckCircle2, QrCode } from "lucide-react";

import { fetchExchange, fetchExchangeQrImage, verifyExchange } from "@/api/exchanges";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QrScanner } from "@/components/QrScanner";
import type { Exchange } from "@/types";

export default function ExchangePage() {
  const { exchangeId } = useParams();

  const [exchange, setExchange] = useState<Exchange | null>(null);
  const [qrImage, setQrImage] = useState<string | null>(null);
  const [manualCode, setManualCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    if (!exchangeId) return;
    fetchExchange(exchangeId)
      .then(setExchange)
      .finally(() => setLoading(false));
  }, [exchangeId]);

  useEffect(() => {
    if (!exchange || exchange.role !== "owner" || exchange.status === "completed") return;
    fetchExchangeQrImage(exchange.id).then(setQrImage);
  }, [exchange]);

  async function handleVerify(code: string) {
    setError(null);
    setVerifying(true);
    try {
      const updated = await verifyExchange(code.trim());
      setExchange(updated);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "That code doesn't match. Please try again.");
    } finally {
      setVerifying(false);
    }
  }

  if (loading) {
    return <div className="container py-16 text-center text-muted-foreground">Loading...</div>;
  }

  if (!exchange) {
    return <div className="container py-16 text-center text-muted-foreground">Exchange not found.</div>;
  }

  if (exchange.status === "completed") {
    return (
      <div className="container max-w-lg py-16 text-center">
        <CheckCircle2 className="mx-auto mb-4 h-12 w-12 text-primary" />
        <h1 className="text-2xl font-semibold">Exchange completed</h1>
        <p className="mt-2 text-muted-foreground">"{exchange.listing_title}" has been handed off. Thanks for using Qoldau!</p>
        <Link to={`/reviews/new/${exchange.id}`} className="mt-6 inline-block font-medium text-primary hover:underline">
          Leave a review
        </Link>
      </div>
    );
  }

  return (
    <div className="container max-w-lg py-12">
      <h1 className="mb-2 flex items-center gap-2 text-2xl font-semibold">
        <QrCode className="h-6 w-6 text-primary" />
        {exchange.listing_title}
      </h1>

      {exchange.role === "owner" ? (
        <>
          <p className="mb-6 text-muted-foreground">
            Show this QR code to the person picking up your item. They'll scan it to confirm the handoff.
          </p>
          <Card>
            <CardContent className="flex flex-col items-center gap-4 p-8">
              {qrImage ? (
                <img src={qrImage} alt="Exchange QR code" className="h-56 w-56" />
              ) : (
                <div className="flex h-56 w-56 items-center justify-center text-muted-foreground">Loading QR...</div>
              )}
            </CardContent>
          </Card>
        </>
      ) : (
        <>
          <p className="mb-6 text-muted-foreground">
            Scan the QR code shown by the owner to confirm you've received the item.
          </p>
          <QrScanner onScan={handleVerify} />

          <div className="my-6 flex items-center gap-3 text-xs text-muted-foreground">
            <div className="h-px flex-1 bg-border" />
            OR ENTER THE CODE MANUALLY
            <div className="h-px flex-1 bg-border" />
          </div>

          <div className="space-y-3">
            <Label htmlFor="manual-code">Confirmation code</Label>
            <Input
              id="manual-code"
              value={manualCode}
              onChange={(e) => setManualCode(e.target.value)}
              placeholder="Paste or type the code"
            />
            <Button
              className="w-full"
              disabled={!manualCode.trim() || verifying}
              onClick={() => handleVerify(manualCode)}
            >
              {verifying ? "Confirming..." : "Confirm exchange"}
            </Button>
          </div>

          {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
        </>
      )}
    </div>
  );
}
