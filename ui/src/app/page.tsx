export default function Home() {
  const url = `http://localhost:6901/?password=password`

  return (
    <div className="w-full min-h-screen">
      <iframe
        src={url}
        className="w-full h-full border-0"
        title="VNC Interface"
        style={{height: '920px', width: '100%'}}
      />
    </div>
  );
}
