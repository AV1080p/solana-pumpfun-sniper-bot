'use client'

import { useState, useEffect, useRef } from 'react'
import { communicationApi, CallSession } from '@/lib/communicationApi'
import { useAuth } from '@/contexts/AuthContext'
import toast from 'react-hot-toast'

interface CallInterfaceProps {
  callSession?: CallSession
  onEndCall?: () => void
}

export function CallInterface({ callSession, onEndCall }: CallInterfaceProps) {
  const { user } = useAuth()
  const [status, setStatus] = useState<string>('initiated')
  const [localStream, setLocalStream] = useState<MediaStream | null>(null)
  const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null)
  const [isMuted, setIsMuted] = useState(false)
  const [isVideoOff, setIsVideoOff] = useState(false)
  const localVideoRef = useRef<HTMLVideoElement>(null)
  const remoteVideoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    if (callSession) {
      setStatus(callSession.status)
      if (callSession.status === 'active') {
        initializeCall()
      }
    }
    return () => {
      // Cleanup streams
      if (localStream) {
        localStream.getTracks().forEach(track => track.stop())
      }
      if (remoteStream) {
        remoteStream.getTracks().forEach(track => track.stop())
      }
    }
  }, [callSession])

  const initializeCall = async () => {
    try {
      // Get user media (simplified - in production, use WebRTC)
      const stream = await navigator.mediaDevices.getUserMedia({
        video: callSession?.call_type === 'video',
        audio: true
      })
      setLocalStream(stream)
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream
      }
    } catch (error) {
      console.error('Error accessing media devices:', error)
      toast.error('Failed to access camera/microphone')
    }
  }

  const handleAccept = async () => {
    if (!callSession) return
    try {
      await communicationApi.updateCallStatus(callSession.session_id, 'active')
      setStatus('active')
      await initializeCall()
    } catch (error: any) {
      toast.error('Failed to accept call')
    }
  }

  const handleReject = async () => {
    if (!callSession) return
    try {
      await communicationApi.updateCallStatus(callSession.session_id, 'ended')
      if (onEndCall) onEndCall()
    } catch (error: any) {
      toast.error('Failed to reject call')
    }
  }

  const handleEndCall = async () => {
    if (!callSession) return
    try {
      await communicationApi.updateCallStatus(callSession.session_id, 'ended')
      if (localStream) {
        localStream.getTracks().forEach(track => track.stop())
      }
      if (onEndCall) onEndCall()
    } catch (error: any) {
      toast.error('Failed to end call')
    }
  }

  const toggleMute = () => {
    if (localStream) {
      localStream.getAudioTracks().forEach(track => {
        track.enabled = isMuted
      })
      setIsMuted(!isMuted)
    }
  }

  const toggleVideo = () => {
    if (localStream) {
      localStream.getVideoTracks().forEach(track => {
        track.enabled = isVideoOff
      })
      setIsVideoOff(!isVideoOff)
    }
  }

  if (!callSession) return null

  return (
    <div className="fixed inset-0 bg-black z-50 flex items-center justify-center">
      <div className="relative w-full h-full">
        {/* Remote Video */}
        {callSession.call_type === 'video' && (
          <video
            ref={remoteVideoRef}
            autoPlay
            playsInline
            className="w-full h-full object-cover"
          />
        )}

        {/* Local Video (Picture-in-Picture) */}
        {callSession.call_type === 'video' && localStream && (
          <div className="absolute top-4 right-4 w-48 h-36 rounded-lg overflow-hidden border-2 border-white shadow-lg">
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
          </div>
        )}

        {/* Call Info Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex flex-col justify-end">
          <div className="p-8 text-center text-white">
            {status === 'ringing' && (
              <>
                <h2 className="text-3xl font-bold mb-2">Incoming Call</h2>
                <p className="text-xl mb-6">
                  {callSession.call_type === 'video' ? 'Video' : 'Voice'} Call
                </p>
                <div className="flex justify-center gap-4">
                  <button
                    onClick={handleAccept}
                    className="bg-green-600 hover:bg-green-700 rounded-full p-4 text-white"
                  >
                    ✓ Accept
                  </button>
                  <button
                    onClick={handleReject}
                    className="bg-red-600 hover:bg-red-700 rounded-full p-4 text-white"
                  >
                    ✕ Reject
                  </button>
                </div>
              </>
            )}

            {status === 'active' && (
              <>
                <h2 className="text-2xl font-bold mb-4">
                  {callSession.call_type === 'video' ? 'Video' : 'Voice'} Call Active
                </h2>
                <div className="flex justify-center gap-4">
                  <button
                    onClick={toggleMute}
                    className={`rounded-full p-4 ${
                      isMuted ? 'bg-red-600' : 'bg-gray-700'
                    } hover:bg-gray-600 text-white`}
                    title={isMuted ? 'Unmute' : 'Mute'}
                  >
                    {isMuted ? '🔇' : '🎤'}
                  </button>
                  {callSession.call_type === 'video' && (
                    <button
                      onClick={toggleVideo}
                      className={`rounded-full p-4 ${
                        isVideoOff ? 'bg-red-600' : 'bg-gray-700'
                      } hover:bg-gray-600 text-white`}
                      title={isVideoOff ? 'Turn on video' : 'Turn off video'}
                    >
                      {isVideoOff ? '📷' : '📹'}
                    </button>
                  )}
                  <button
                    onClick={handleEndCall}
                    className="bg-red-600 hover:bg-red-700 rounded-full p-4 text-white"
                  >
                    ✕ End Call
                  </button>
                </div>
              </>
            )}

            {status === 'initiated' && (
              <div className="text-center">
                <p className="text-xl mb-4">Calling...</p>
                <button
                  onClick={handleEndCall}
                  className="bg-red-600 hover:bg-red-700 rounded-full p-4 text-white"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

