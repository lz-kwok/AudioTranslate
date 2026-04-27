
import os
import torch
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

def test_campplus():
    print("Testing standalone CAM++ Speaker Verification...")
    try:
        # This is a speaker verification model, used to extract embeddings
        sv_pipeline = pipeline(
            task=Tasks.speaker_verification,
            model='damo/speech_campplus_sv_zh-cn_16k-common'
        )
        print("Pipeline initialized!")
        
        # Test on a dummy or small audio if available
        # But even initialization is a good sign
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_campplus()
