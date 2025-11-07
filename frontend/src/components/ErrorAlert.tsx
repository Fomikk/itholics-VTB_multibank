/** Error alert component */
interface ErrorAlertProps {
  message: string
  onClose?: () => void
}

export default function ErrorAlert({ message, onClose }: ErrorAlertProps) {
  return (
    <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded relative">
      <span className="block sm:inline">{message}</span>
      {onClose && (
        <button
          className="absolute top-0 bottom-0 right-0 px-4 py-3"
          onClick={onClose}
        >
          <span className="text-red-800">×</span>
        </button>
      )}
    </div>
  )
}

