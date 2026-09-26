"""Selected heartbeat function logic, pinned 872a4514, turn280file0.
Only imports/type annotations are simplified; this is not the full service.
"""
import threading
from copy import deepcopy
STRICT_MAPPING_RESPONSE_PROMPT_VERSIONS=frozenset()
class MonitoringAiOutputValidationError(ValueError): pass

def _run_with_heartbeat(self,job,owner,provider,envelope):
    stop=threading.Event()
    heartbeat_error=[]
    interval=max(0.25,min(30.0,float(self.repository.lease_seconds)/3.0))
    def heartbeat_loop():
        while not stop.wait(interval):
            try:
                self.repository.heartbeat(job.project_id,job.job_id,owner)
            except Exception as exc:
                heartbeat_error.append(exc)
                return
    self.repository.heartbeat(job.project_id,job.job_id,owner)
    thread=threading.Thread(target=heartbeat_loop,name=f"monitoring-ai-heartbeat-{job.job_id[:12]}",daemon=True)
    thread.start()
    call_error=[]
    try:
        output=provider.run(envelope)
    except Exception as exc:
        call_error.append(exc)
        raise
    finally:
        stop.set()
        thread.join(timeout=max(1.0,interval+0.5))
        call_diagnostics=deepcopy(getattr(provider,"response_diagnostics",{}) or {})
        try:
            self.repository.record_call(project_id=job.project_id,job_id=job.job_id,attempt_id=owner,call_seq=0,owner=owner,provider=job.provider,requested_model=job.requested_model,observed_model=str(getattr(provider,"response_model","") or ""),diagnostics=call_diagnostics,outcome="success" if not call_error else "provider_error",error_code=type(call_error[0]).__name__ if call_error else "")
        except Exception:
            import logging
            logging.getLogger(__name__).warning("call ledger write failed for job %s; metering incomplete for this physical call",job.job_id)
    if job.prompt_version in STRICT_MAPPING_RESPONSE_PROMPT_VERSIONS and isinstance(output,str):
        return {"invalid_response_text":output,"response_diagnostics":deepcopy(getattr(provider,"strict_response_diagnostics",{}))}
    if not isinstance(output,dict):
        raise MonitoringAiOutputValidationError("provider output must be a JSON object")
    return output
