import Vision
import AppKit
// usage: swift mask.swift <in.jpg> <out-mask.png>
let a = CommandLine.arguments
let url = URL(fileURLWithPath: a[1])
let req = VNGeneratePersonSegmentationRequest()
req.qualityLevel = .accurate
req.outputPixelFormat = kCVPixelFormatType_OneComponent8
try VNImageRequestHandler(url: url).perform([req])
let buf = req.results!.first!.pixelBuffer
let ci = CIImage(cvPixelBuffer: buf)
let rep = NSBitmapImageRep(cgImage: CIContext().createCGImage(ci, from: ci.extent)!)
try rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: a[2]))
print("mask", ci.extent.size)
