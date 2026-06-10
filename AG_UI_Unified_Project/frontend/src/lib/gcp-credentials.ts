import { Storage } from "@google-cloud/storage";
import { existsSync } from "fs";
import path from "path";

type GcpStorageOptions = ConstructorParameters<typeof Storage>[0];

export function getGcpStorageOptions(): GcpStorageOptions {
  const projectId = process.env.GOOGLE_CLOUD_PROJECT;
  const credsB64 = process.env.GOOGLE_APPLICATION_CREDENTIALS_BASE64;

  if (credsB64) {
    const credentials = JSON.parse(
      Buffer.from(credsB64, "base64").toString("utf-8")
    );
    return { credentials, projectId };
  }

  const credsPath = process.env.GOOGLE_APPLICATION_CREDENTIALS;
  if (credsPath) {
    const resolved = path.resolve(process.cwd(), credsPath);
    if (!existsSync(resolved)) {
      throw new Error(`Credenciales GCP no encontradas en: ${resolved}`);
    }
    return { keyFilename: resolved, projectId };
  }

  return { projectId };
}

export function getStorage(): Storage {
  return new Storage(getGcpStorageOptions());
}
