import { NextRequest, NextResponse } from "next/server";
import { getStorage } from "@/lib/gcp-credentials";

export const maxDuration = 120;
export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  try {
    const bucketName = process.env.GCS_BUCKET_RESUMEN;
    if (!bucketName) {
      return NextResponse.json(
        { error: "GCS_BUCKET_RESUMEN no está definido en .env" },
        { status: 500 }
      );
    }

    const formData = await req.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ error: "No file" }, { status: 400 });
    }

    const filename = `uploads/${Date.now()}-${file.name.replace(/[^a-zA-Z0-9._-]/g, "_")}`;
    const storage = getStorage();
    const gcsFile = storage.bucket(bucketName).file(filename);

    const buffer = Buffer.from(await file.arrayBuffer());
    await gcsFile.save(buffer, {
      metadata: { contentType: file.type || "application/octet-stream" },
      resumable: false,
    });

    return NextResponse.json({
      url: `gs://${bucketName}/${filename}`,
      mimeType: file.type,
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Upload failed";
    console.error("Upload error:", error);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
