import SwiftUI

struct CatStretchView: View {
    let totalPoints: Int
    @State private var isAnimating = false

    var milestone: CatMilestone {
        CatMilestone.milestone(for: totalPoints)
    }

    var body: some View {
        VStack(spacing: 0) {
            ZStack {
                // 背景
                backgroundView
                    .frame(maxWidth: .infinity)
                    .frame(height: 500)

                // 猫本体
                VStack(spacing: 0) {
                    Spacer()

                    // 猫の頭
                    catHead

                    // 猫の伸びる胴体
                    catBody
                        .frame(height: isAnimating ? milestone.height : 80)
                        .animation(.spring(response: 1.0, dampingFraction: 0.6), value: isAnimating)

                    // 猫の足
                    catFeet
                }
                .padding(.bottom, 40)
            }

            // マイルストーン情報
            milestoneInfo
                .padding()
        }
        .onAppear {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                isAnimating = true
            }
        }
    }

    private var backgroundView: some View {
        ZStack {
            // グラデーション背景
            LinearGradient(
                gradient: Gradient(colors: [
                    milestone.backgroundColor,
                    milestone.backgroundColor.opacity(0.3)
                ]),
                startPoint: .top,
                endPoint: .bottom
            )

            // マイルストーンに応じた装飾
            if milestone == .space {
                ForEach(0..<20, id: \.self) { _ in
                    Circle()
                        .fill(Color.white)
                        .frame(width: CGFloat.random(in: 2...4))
                        .position(
                            x: CGFloat.random(in: 0...UIScreen.main.bounds.width),
                            y: CGFloat.random(in: 0...400)
                        )
                }
            }

            // マイルストーンアイコン
            if milestone != .normal {
                Text(milestone.emoji)
                    .font(.system(size: milestone == .space ? 100 : 80))
                    .opacity(0.3)
                    .offset(y: -50)
            }
        }
    }

    private var catHead: some View {
        ZStack {
            // 頭
            Circle()
                .fill(
                    LinearGradient(
                        gradient: Gradient(colors: [Color.orange.opacity(0.8), Color.orange]),
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )
                .frame(width: 60, height: 60)

            // 耳（左）
            Triangle()
                .fill(Color.orange)
                .frame(width: 20, height: 25)
                .offset(x: -20, y: -20)

            // 耳（右）
            Triangle()
                .fill(Color.orange)
                .frame(width: 20, height: 25)
                .offset(x: 20, y: -20)

            // 顔
            HStack(spacing: 12) {
                // 目（左）
                Circle()
                    .fill(Color.black)
                    .frame(width: 8, height: 8)

                // 目（右）
                Circle()
                    .fill(Color.black)
                    .frame(width: 8, height: 8)
            }
            .offset(y: -5)

            // 口
            Text("ω")
                .font(.system(size: 14))
                .offset(y: 10)
        }
    }

    private var catBody: some View {
        ZStack {
            // 胴体の縞模様
            VStack(spacing: 5) {
                ForEach(0..<Int(milestone.height / 15), id: \.self) { index in
                    Rectangle()
                        .fill(
                            index % 2 == 0 ?
                            Color.orange.opacity(0.7) :
                            Color.orange.opacity(0.9)
                        )
                        .frame(height: 10)
                }
            }

            // 胴体のメインカラー
            Rectangle()
                .fill(
                    LinearGradient(
                        gradient: Gradient(colors: [
                            Color.orange.opacity(0.9),
                            Color.orange.opacity(0.7)
                        ]),
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .frame(width: 50)
                .overlay(
                    Rectangle()
                        .stroke(Color.orange.opacity(0.5), lineWidth: 2)
                )
        }
    }

    private var catFeet: some View {
        HStack(spacing: 20) {
            // 左足
            Capsule()
                .fill(Color.orange)
                .frame(width: 15, height: 30)

            // 右足
            Capsule()
                .fill(Color.orange)
                .frame(width: 15, height: 30)
        }
    }

    private var milestoneInfo: some View {
        VStack(spacing: 8) {
            HStack {
                Text(milestone.title)
                    .font(.headline)
                Text(milestone.emoji)
                    .font(.title2)
            }

            Text("\(totalPoints) pt")
                .font(.title)
                .fontWeight(.bold)
                .foregroundStyle(.orange)

            if let nextMilestone = milestone.nextMilestone {
                Text("次のマイルストーン: \(nextMilestone) pt")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                ProgressView(value: Double(totalPoints), total: Double(nextMilestone))
                    .tint(.orange)
                    .frame(width: 200)
            } else {
                Text("最高到達点！")
                    .font(.caption)
                    .foregroundStyle(.orange)
                    .fontWeight(.semibold)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 8)
    }
}

// 三角形の形状（耳用）
struct Triangle: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        path.move(to: CGPoint(x: rect.midX, y: rect.minY))
        path.addLine(to: CGPoint(x: rect.minX, y: rect.maxY))
        path.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY))
        path.closeSubpath()
        return path
    }
}
