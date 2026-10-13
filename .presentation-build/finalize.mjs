import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {finalizePresentation} from 'file:///C:/Users/babur/.codex/plugins/cache/openai-primary-runtime/presentations/26.1009.11318/skills/presentations/container_tools/artifact_tool_utils.mjs';
const dir=path.dirname(fileURLToPath(import.meta.url)),root=path.dirname(dir);
const skill='C:/Users/babur/.codex/plugins/cache/openai-primary-runtime/presentations/26.1009.11318/skills/presentations';
process.env.RUNTIME_NODE_MODULES='C:/Users/babur/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const result=await finalizePresentation({workspaceDir:root,candidatePath:path.join(dir,'candidate.pptx'),finalPath:path.join(root,'output/presentations/MentorPulse_Refactored.pptx'),pythonExecutable:'C:/Users/babur/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],fontPolicy:{basis:'design',families:['Arial']},requiredNativeTableOwnerSlides:[4,9,10,11,12,13],explicitTotalSlideCount:16,verifyArtifactToolImport:true,receiptPath:path.join(dir,'validation.json')});
console.log(JSON.stringify(result));
