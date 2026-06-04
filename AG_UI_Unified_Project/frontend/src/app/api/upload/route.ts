import { NextRequest, NextResponse } from "next/server";
import { Storage } from "@google-cloud/storage";
import { Readable } from "stream";

const storage = new Storage();
const BUCKET = process.env.GCS_BUCKET_RESUMEN!;

export const maxDuration = 120;

export async function POST(req: NextRequest) {
  try {
    if (!BUCKET) {
      return NextResponse.json(
        { error: "GCS_BUCKET_RESUMEN no está definido en .env.local" },
        { status: 500 }
      );
    }

    const formData = await req.formData();
    const file = formData.get("file") as File;

    if (!file) {
      return NextResponse.json({ error: "No file" }, { status: 400 });
    }

    const filename = `uploads/${Date.now()}-${file.name.replace(/[^a-zA-Z0-9._-]/g, "_")}`;
    const bucket = storage.bucket(BUCKET);
    const gcsFile = bucket.file(filename);

    const writeStream = gcsFile.createWriteStream({
      metadata: { contentType: file.type },
      resumable: false,
    });

    const reader = file.stream().getReader();
    const nodeStream = new Readable({
      async read() {
        const { done, value } = await reader.read();
        if (done) {
          this.push(null);
        } else {
          this.push(Buffer.from(value));
        }
      },
    });

    await new Promise<void>((resolve, reject) => {
      nodeStream.pipe(writeStream);
      writeStream.on("finish", resolve);
      writeStream.on("error", reject);
      nodeStream.on("error", reject);
    });

    return NextResponse.json({
      url: `gs://${BUCKET}/${filename}`,
      mimeType: file.type,
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Upload failed";
    console.error("Upload error:", error);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
