export default function Home() {
  return (
    <div className="w-full min-h-screen">
      <iframe
        src="http://localhost:6080/vnc.html"
        className="w-full h-full border-0"
        title="VNC Interface"
        style={{height: '920px', width: '100%'}}
      />
    </div>
  );
}
