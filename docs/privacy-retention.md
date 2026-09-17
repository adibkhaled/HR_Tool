# Privacy and retention

Resumes, job descriptions, extracted text, embeddings, match snapshots, chat history, and audit records can contain sensitive employment data. Keep source storage private, encrypt transport and storage through the deployment platform, restrict tenant access, and redact logs and provider diagnostics.

Retention duration, jurisdiction, deletion approval, object-storage lifecycle, and provider data-use settings are deployment gates. A deletion workflow must reconcile the source file, active and stale chunks, embeddings, derived match evidence, chat references, and audit lineage. Audit records should preserve the action and outcome without retaining unnecessary source content.

The system is decision support for human review. It must not infer protected characteristics or make automated hiring, rejection, offer, or employment decisions.
